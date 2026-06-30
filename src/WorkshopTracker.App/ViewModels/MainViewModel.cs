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
    private string _status = "Укажите путь к Excel-файлу и выполните импорт";
    private ProductSnapshot? _selectedProduct;

    public ObservableCollection<ProductSnapshot> Products { get; } = new();
    public ObservableCollection<ImportIssue> Issues { get; } = new();
    public string ExcelPath { get => _excelPath; set { _excelPath = value; OnChanged(); } }
    public string Status { get => _status; set { _status = value; OnChanged(); } }
    public ProductSnapshot? SelectedProduct { get => _selectedProduct; set { _selectedProduct = value; OnChanged(); } }
    public string SearchText { get; set; } = string.Empty;

    public async Task ImportAsync()
    {
        await _cache.InitializeAsync();
        _cache.BackupIfExists();
        try
        {
            Status = "Импорт данных...";
            var result = await _importer.ImportAsync(ExcelPath);
            await _cache.ReplaceSnapshotsAsync(result.Products, result.Incoming, result.Report);
            Products.Clear(); foreach (var p in result.Products.OrderByDescending(p => p.StatusDate).ThenBy(p => p.Name)) Products.Add(p);
            Issues.Clear(); foreach (var issue in result.Report.Issues) Issues.Add(issue);
            Status = $"Импорт выполнен: листов {result.Report.SheetsRead}, изделий {result.Report.ProductsRecognized}, предупреждений {result.Report.Issues.Count}";
        }
        catch (Exception ex)
        {
            Status = $"Импорт завершён с ошибкой. Данные не обновлены. Причина: {ex.Message}";
        }
    }

    public IEnumerable<ProductSnapshot> FilteredProducts() => string.IsNullOrWhiteSpace(SearchText)
        ? Products
        : Products.Where(p => TextNormalizer.Normalize(string.Join(' ', p.Name, p.Designation, p.SerialNumber, p.WorkOrder, p.Contract, p.Status, p.Note)).Contains(TextNormalizer.Normalize(SearchText)));

    public event PropertyChangedEventHandler? PropertyChanged;
    private void OnChanged([CallerMemberName] string? name = null) => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
}
