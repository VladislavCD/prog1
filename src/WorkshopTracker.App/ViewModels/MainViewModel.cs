using System.IO;
using System.Collections.ObjectModel;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using WorkshopTracker.App.Models;
using WorkshopTracker.App.Services;

namespace WorkshopTracker.App.ViewModels;

public sealed class MainViewModel : INotifyPropertyChanged
{
    private readonly string _dataDirectory;
    private readonly LocalCache _cache;
    private readonly ExcelImportService _importer = new();
    private string _excelPath = string.Empty;
    private string _status;
    private string _searchText = string.Empty;
    private bool _isImporting;
    private ProductSnapshot? _selectedProduct;

    public MainViewModel()
    {
        _dataDirectory = GetWritableAppDataDirectory();
        _cache = new LocalCache(Path.Combine(_dataDirectory, "cache.sqlite"));
        _status = $"\u041F\u0430\u043F\u043A\u0430 \u0434\u0430\u043D\u043D\u044B\u0445: {_dataDirectory}. \u0412\u044B\u0431\u0435\u0440\u0438\u0442\u0435 Excel-\u0444\u0430\u0439\u043B \u0438\u043B\u0438 \u0432\u0441\u0442\u0430\u0432\u044C\u0442\u0435 \u043F\u0443\u0442\u044C \u043A .xlsx";
    }

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
            Status = "\u041F\u0440\u043E\u0432\u0435\u0440\u043A\u0430 Excel-\u0444\u0430\u0439\u043B\u0430...";
            ValidateExcelPath();
            await WriteLogAsync($"START {ExcelPath}");

            try
            {
                await _cache.InitializeAsync();
                _cache.BackupIfExists();
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException($"\u041D\u0435 \u0443\u0434\u0430\u043B\u043E\u0441\u044C \u043F\u043E\u0434\u0433\u043E\u0442\u043E\u0432\u0438\u0442\u044C \u043B\u043E\u043A\u0430\u043B\u044C\u043D\u044B\u0439 \u043A\u044D\u0448 SQLite \u0432 \u043F\u0430\u043F\u043A\u0435 {_dataDirectory}: {ex.Message}", ex);
            }

            ImportResult result;
            try
            {
                Status = "\u0418\u043C\u043F\u043E\u0440\u0442 \u0434\u0430\u043D\u043D\u044B\u0445 \u0438\u0437 \u0432\u0440\u0435\u043C\u0435\u043D\u043D\u043E\u0439 \u043A\u043E\u043F\u0438\u0438 Excel...";
                result = await _importer.ImportAsync(ExcelPath, _dataDirectory);
                await _cache.ReplaceSnapshotsAsync(result.Products, result.Incoming, result.Report);
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException($"\u041D\u0435 \u0443\u0434\u0430\u043B\u043E\u0441\u044C \u043F\u0440\u043E\u0447\u0438\u0442\u0430\u0442\u044C Excel \u0438\u043B\u0438 \u0441\u043E\u0445\u0440\u0430\u043D\u0438\u0442\u044C \u0434\u0430\u043D\u043D\u044B\u0435 \u0432 \u043A\u044D\u0448. \u0424\u0430\u0439\u043B: {ExcelPath}. \u041F\u0430\u043F\u043A\u0430 \u0434\u0430\u043D\u043D\u044B\u0445: {_dataDirectory}. \u041F\u043E\u0434\u0440\u043E\u0431\u043D\u043E\u0441\u0442\u0438: {ex.Message}", ex);
            }

            Products.Clear();
            foreach (var p in result.Products.OrderByDescending(p => p.StatusDate).ThenBy(p => p.Name)) Products.Add(p);
            Issues.Clear();
            foreach (var issue in result.Report.Issues) Issues.Add(issue);
            OnChanged(nameof(FilteredProducts));

            Status = $"\u0418\u043C\u043F\u043E\u0440\u0442 \u0432\u044B\u043F\u043E\u043B\u043D\u0435\u043D: \u043B\u0438\u0441\u0442\u043E\u0432 {result.Report.SheetsRead}, \u0441\u0442\u0440\u043E\u043A {result.Report.RowsProcessed}, \u0438\u0437\u0434\u0435\u043B\u0438\u0439 {result.Report.ProductsRecognized}, \u043F\u0440\u0435\u0434\u0443\u043F\u0440\u0435\u0436\u0434\u0435\u043D\u0438\u0439 {result.Report.Issues.Count}. \u041F\u0430\u043F\u043A\u0430 \u0434\u0430\u043D\u043D\u044B\u0445: {_dataDirectory}";
            await WriteLogAsync($"OK sheets={result.Report.SheetsRead} rows={result.Report.RowsProcessed} products={result.Report.ProductsRecognized}");
        }
        catch (Exception ex)
        {
            Status = $"\u0418\u043C\u043F\u043E\u0440\u0442 \u043D\u0435 \u0432\u044B\u043F\u043E\u043B\u043D\u0435\u043D. \u0414\u0430\u043D\u043D\u044B\u0435 \u043D\u0435 \u043E\u0431\u043D\u043E\u0432\u043B\u0435\u043D\u044B. {BuildUserMessage(ex)}";
            await WriteLogAsync($"ERROR {Status}");
        }
        finally
        {
            IsImporting = false;
        }
    }

    private void ValidateExcelPath()
    {
        if (string.IsNullOrWhiteSpace(ExcelPath))
            throw new InvalidOperationException("\u0421\u043D\u0430\u0447\u0430\u043B\u0430 \u0432\u044B\u0431\u0435\u0440\u0438\u0442\u0435 Excel-\u0444\u0430\u0439\u043B \u043A\u043D\u043E\u043F\u043A\u043E\u0439 \u00AB\u0412\u044B\u0431\u0440\u0430\u0442\u044C \u0444\u0430\u0439\u043B\u2026\u00BB \u0438\u043B\u0438 \u0432\u0441\u0442\u0430\u0432\u044C\u0442\u0435 \u043F\u043E\u043B\u043D\u044B\u0439 \u043F\u0443\u0442\u044C \u043A .xlsx.");
        if (!File.Exists(ExcelPath))
            throw new FileNotFoundException("\u0424\u0430\u0439\u043B \u043D\u0435 \u043D\u0430\u0439\u0434\u0435\u043D. \u041F\u0440\u043E\u0432\u0435\u0440\u044C\u0442\u0435 \u043F\u0443\u0442\u044C \u0438\u043B\u0438 \u0432\u044B\u0431\u0435\u0440\u0438\u0442\u0435 \u0444\u0430\u0439\u043B \u0447\u0435\u0440\u0435\u0437 \u043A\u043D\u043E\u043F\u043A\u0443 \u00AB\u0412\u044B\u0431\u0440\u0430\u0442\u044C \u0444\u0430\u0439\u043B\u2026\u00BB.", ExcelPath);
        if (!Path.GetExtension(ExcelPath).Equals(".xlsx", StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("\u041D\u0443\u0436\u043D\u043E \u0432\u044B\u0431\u0440\u0430\u0442\u044C \u0444\u0430\u0439\u043B Excel \u0432 \u0444\u043E\u0440\u043C\u0430\u0442\u0435 .xlsx.");
    }

    private static string BuildUserMessage(Exception ex) => ex switch
    {
        UnauthorizedAccessException => $"\u041D\u0435\u0442 \u043F\u0440\u0430\u0432 \u0434\u043E\u0441\u0442\u0443\u043F\u0430. \u041F\u043E\u0434\u0440\u043E\u0431\u043D\u043E\u0441\u0442\u0438 Windows: {ex.Message}",
        IOException => $"\u0424\u0430\u0439\u043B \u0438\u043B\u0438 \u043B\u043E\u043A\u0430\u043B\u044C\u043D\u044B\u0439 \u043A\u044D\u0448 \u043D\u0435\u0434\u043E\u0441\u0442\u0443\u043F\u0435\u043D: {ex.Message}",
        InvalidOperationException when ex.InnerException is UnauthorizedAccessException inner => $"\u041D\u0435\u0442 \u043F\u0440\u0430\u0432 \u0434\u043E\u0441\u0442\u0443\u043F\u0430. {ex.Message}. \u041F\u043E\u0434\u0440\u043E\u0431\u043D\u043E\u0441\u0442\u0438 Windows: {inner.Message}",
        InvalidOperationException when MentionsPassword(ex) => $"\u041A\u043D\u0438\u0433\u0430 \u0441 \u043F\u0430\u0440\u043E\u043B\u0435\u043C \u043D\u0430 \u0437\u0430\u043F\u0438\u0441\u044C \u043F\u043E\u0434\u0434\u0435\u0440\u0436\u0438\u0432\u0430\u0435\u0442\u0441\u044F \u0438 \u0447\u0438\u0442\u0430\u0435\u0442\u0441\u044F \u0442\u043E\u043B\u044C\u043A\u043E \u0434\u043B\u044F \u0447\u0442\u0435\u043D\u0438\u044F. \u0415\u0441\u043B\u0438 Excel \u043F\u0440\u043E\u0441\u0438\u0442 \u043F\u0430\u0440\u043E\u043B\u044C \u0438\u043C\u0435\u043D\u043D\u043E \u043D\u0430 \u043E\u0442\u043A\u0440\u044B\u0442\u0438\u0435 \u0444\u0430\u0439\u043B\u0430, \u0442\u0430\u043A\u043E\u0439 \u0444\u0430\u0439\u043B \u0440\u0430\u0441\u0448\u0438\u0444\u0440\u043E\u0432\u0430\u0442\u044C \u043D\u0435\u043B\u044C\u0437\u044F: {ex.Message}",
        InvalidOperationException => ex.Message,
        _ => ex.Message
    };

    private static bool MentionsPassword(Exception ex)
    {
        var text = $"{ex.Message} {ex.InnerException?.Message}".ToLowerInvariant();
        return text.Contains("password") || text.Contains("\u043F\u0430\u0440\u043E\u043B");
    }

    private async Task WriteLogAsync(string message)
    {
        try
        {
            var logDir = Path.Combine(_dataDirectory, "logs");
            Directory.CreateDirectory(logDir);
            await File.AppendAllTextAsync(Path.Combine(logDir, "import.log"), $"{DateTime.Now:yyyy-MM-dd HH:mm:ss} {message}{Environment.NewLine}");
        }
        catch
        {
            // Logging must never break import or UI feedback.
        }
    }

    private static string GetWritableAppDataDirectory()
    {
        var baseDir = AppContext.BaseDirectory;
        var currentDir = Environment.CurrentDirectory;
        var userProfile = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
        var candidates = new[]
        {
            Path.Combine(baseDir, "WorkshopTrackerData"),
            Path.Combine(currentDir, "WorkshopTrackerData"),
            string.IsNullOrWhiteSpace(userProfile) ? null : Path.Combine(userProfile, "WorkshopTrackerData")
        };

        foreach (var candidate in candidates.Where(c => !string.IsNullOrWhiteSpace(c)))
        {
            try
            {
                Directory.CreateDirectory(candidate!);
                var probe = Path.Combine(candidate!, $"workshop-tracker-write-test-{Guid.NewGuid():N}.tmp");
                File.WriteAllText(probe, "ok");
                File.Delete(probe);
                return candidate!;
            }
            catch
            {
                // Try the next app-owned location.
            }
        }

        throw new InvalidOperationException("\u041D\u0435 \u0443\u0434\u0430\u043B\u043E\u0441\u044C \u043D\u0430\u0439\u0442\u0438 \u0434\u043E\u0441\u0442\u0443\u043F\u043D\u0443\u044E \u043F\u0430\u043F\u043A\u0443 \u0434\u043B\u044F \u0434\u0430\u043D\u043D\u044B\u0445 \u043F\u0440\u0438\u043B\u043E\u0436\u0435\u043D\u0438\u044F \u0440\u044F\u0434\u043E\u043C \u0441 \u043F\u0440\u043E\u0433\u0440\u0430\u043C\u043C\u043E\u0439 \u0438\u043B\u0438 \u0432 \u043F\u0440\u043E\u0444\u0438\u043B\u0435 \u043F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u0435\u043B\u044F.");
    }

    public event PropertyChangedEventHandler? PropertyChanged;
    private void OnChanged([CallerMemberName] string? name = null) => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(name));
}
