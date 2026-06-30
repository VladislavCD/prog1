using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using WorkshopTracker.App.Models;
using WorkshopTracker.App.Services;

namespace WorkshopTracker.App.ViewModels;

public sealed class MainViewModel : INotifyPropertyChanged
{
    private readonly LocalCache _cache = new(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "WorkshopTracker", "cache.sqlite"));
    private readonly ExcelImportService _importer = new();
    private string _excelPath = string.Empty;
    private string _status = "Нажмите «Выбрать файл…» или вставьте путь к .xlsx";
    private string _searchText = string.Empty;
    private bool _isImporting;
    private ProductSnapshot? _selectedProduct;

    public ObservableCollection<ProductSnapshot> Products { get; } = new();
    public ObservableCollection<ImportIssue> Issues { get; } = new();
    public string ExcelPath { get => _excelPath; set { _excelPath = value.Trim('"'); OnChanged(); } }
    public string Status { get => _status; private set { _status = value; OnChanged(); } }
    public string SearchText { get => _searchText; set { _searchText = value; OnChanged(); OnChanged(nameof(FilteredProducts)); } }
    public bool IsImporting { get => _isImporting; private set { _isImporting = value; OnChanged(); } }
    public ProductSnapshot? SelectedProduct { get => _selectedProduct; set { _selectedProduct = value; OnChanged(); } }
    public IEnumerable<ProductSnapshot> FilteredProducts => string.IsNullOrWhiteSpace(SearchText)
        ? Products
        : Products.Where(p => TextNormalizer.Normalize(string.Join(' ', p.Name, p.Designation, p.SerialNumber, p.WorkOrder, p.Contract, p.Status, p.Note)).Contains(TextNormalizer.Normalize(SearchText)));

    public async Task ImportAsync()
    {
        if (IsImporting) return;
        try
        {
            IsImporting = true;
            Status = "Проверка Excel-файла...";
            ValidateExcelPath();

            try
            {
                await _cache.InitializeAsync();
                _cache.BackupIfExists();
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException($"Не удалось подготовить локальный кэш SQLite: {ex.Message}", ex);
            }

            ImportResult result;
            try
            {
                Status = "Импорт данных из временной копии Excel...";
                result = await _importer.ImportAsync(ExcelPath);
                await _cache.ReplaceSnapshotsAsync(result.Products, result.Incoming, result.Report);
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException($"Не удалось прочитать Excel или сохранить данные в кэш. Файл: {ExcelPath}. Подробности: {ex.Message}", ex);
            }

            Products.Clear();
            foreach (var p in result.Products.OrderByDescending(p => p.StatusDate).ThenBy(p => p.Name)) Products.Add(p);
            Issues.Clear();
            foreach (var issue in result.Report.Issues) Issues.Add(issue);
            OnChanged(nameof(FilteredProducts));

            Status = $"Импорт выполнен: листов {result.Report.SheetsRead}, строк {result.Report.RowsProcessed}, изделий {result.Report.ProductsRecognized}, предупреждений {result.Report.Issues.Count}";
        }
        catch (Exception ex)
        {
            Status = $"Импорт не выполнен. Данные не обновлены. {BuildUserMessage(ex)}";
        }
        finally
        {
            IsImporting = false;
        }
    }

    private void ValidateExcelPath()
    {
        if (string.IsNullOrWhiteSpace(ExcelPath))
            throw new InvalidOperationException("Сначала выберите Excel-файл кнопкой «Выбрать файл…» или вставьте полный путь к .xlsx.");
        if (!File.Exists(ExcelPath))
            throw new FileNotFoundException("Файл не найден. Проверьте путь или выберите файл через кнопку «Выбрать файл…».", ExcelPath);
        if (!Path.GetExtension(ExcelPath).Equals(".xlsx", StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Нужно выбрать файл Excel в формате .xlsx.");
    }

    private static string BuildUserMessage(Exception ex) => ex switch
    {
        UnauthorizedAccessException => $"Нет прав доступа. Подробности Windows: {ex.Message}",
        IOException => $"Файл или локальный кэш недоступен: {ex.Message}",
        InvalidOperationException when ex.InnerException is UnauthorizedAccessException inner => $"Нет прав доступа. {ex.Message}. Подробности Windows: {inner.Message}",
        InvalidOperationException when MentionsPassword(ex) => $"Книга с паролем на запись поддерживается и читается только для чтения. Если Excel просит пароль именно на открытие файла, такой файл расшифровать нельзя: {ex.Message}",
        InvalidOperationException => ex.Message,
        _ => ex.Message
    };

    private static bool MentionsPassword(Exception ex)
    {
        var text = $"{ex.Message} {ex.InnerException?.Message}".ToLowerInvariant();
        return text.Contains("password") || text.Contains("парол");
    }

    public event PropertyChangedEventHandler? PropertyChanged;
    private void OnChanged([CallerMemberName] string? name = null) => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
}
