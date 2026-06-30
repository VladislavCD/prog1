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

            await _cache.InitializeAsync();
            _cache.BackupIfExists();

            Status = "Импорт данных из временной копии Excel...";
            var result = await _importer.ImportAsync(ExcelPath);
            await _cache.ReplaceSnapshotsAsync(result.Products, result.Incoming, result.Report);

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
        UnauthorizedAccessException => "Нет прав на чтение Excel-файла или запись локального кэша.",
        IOException => $"Excel-файл недоступен или занят другим приложением: {ex.Message}",
        _ => ex.Message
    };

    public event PropertyChangedEventHandler? PropertyChanged;
    private void OnChanged([CallerMemberName] string? name = null) => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
}
