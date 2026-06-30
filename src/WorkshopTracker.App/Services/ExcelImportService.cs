using System.IO;
using ClosedXML.Excel;
using WorkshopTracker.App.Models;

namespace WorkshopTracker.App.Services;

public sealed class ExcelImportService
{
    public async Task<ImportResult> ImportAsync(string excelPath, CancellationToken ct = default)
    {
        if (!File.Exists(excelPath)) throw new FileNotFoundException("Excel-\u0444\u0430\u0439\u043B \u043D\u0435 \u043D\u0430\u0439\u0434\u0435\u043D", excelPath);
        var importedAt = DateTime.Now;
        var temp = Path.Combine(Path.GetTempPath(), $"workshop-tracker-{Guid.NewGuid():N}.xlsx");
        await CopyWorkbookToTempAsync(excelPath, temp, ct);
        try
        {
            return await Task.Run(() => ReadWorkbook(temp, excelPath, importedAt, ct), ct);
        }
        finally
        {
            try
            {
                if (File.Exists(temp)) File.SetAttributes(temp, FileAttributes.Normal);
                File.Delete(temp);
            }
            catch { /* temp cleanup best effort */ }
        }
    }

    private static async Task CopyWorkbookToTempAsync(string sourcePath, string tempPath, CancellationToken ct)
    {
        await using var source = new FileStream(sourcePath, FileMode.Open, FileAccess.Read, FileShare.ReadWrite | FileShare.Delete);
        await using var target = new FileStream(tempPath, FileMode.CreateNew, FileAccess.Write, FileShare.None);
        await source.CopyToAsync(target, ct);
        File.SetAttributes(tempPath, File.GetAttributes(tempPath) | FileAttributes.ReadOnly);
    }

    private static ImportResult ReadWorkbook(string tempPath, string sourcePath, DateTime importedAt, CancellationToken ct)
    {
        using var stream = new FileStream(tempPath, FileMode.Open, FileAccess.Read, FileShare.Read);
        using var wb = new XLWorkbook(stream);
        var products = new List<ProductSnapshot>();
        var incoming = new List<IncomingItem>();
        var issues = new List<ImportIssue>();
        var rows = 0;
        foreach (var ws in wb.Worksheets)
        {
            ct.ThrowIfCancellationRequested();
            var used = ws.RangeUsed();
            if (used is null) continue;
            foreach (var row in used.RowsUsed())
            {
                rows++;
                var values = row.Cells(1, Math.Min(12, used.ColumnCount())).Select(c => c.GetFormattedString()).ToArray();
                if (values.All(string.IsNullOrWhiteSpace)) continue;
                var joined = string.Join(' ', values).Trim();
                if (LooksLikeHeader(joined)) continue;
                var source = new ExcelSourceRef(Path.GetFileName(sourcePath), ws.Name, row.RowNumber(), $"A{row.RowNumber()}:{ColumnName(used.ColumnCount())}{row.RowNumber()}", importedAt);
                var serial = FirstMatch(values, v => v.Any(char.IsDigit) && v.Length is >= 5 and <= 20);
                var designation = FirstMatch(values, v => v.Any(char.IsLetter) && v.Any(char.IsDigit));
                var status = values.FirstOrDefault(v => TextNormalizer.Normalize(v) is var n && (n.Contains("\u041F\u0421\u0418") || n.Contains("\u041E\u0422\u041A") || n.Contains("\u0423\u041F\u0410\u041A") || n.Contains("\u0413\u041E\u0422\u041E") || n.Contains("\u0426\u0415\u0425") || n.Contains("\u0421\u041A\u041B")));
                var name = values.FirstOrDefault(v => !string.IsNullOrWhiteSpace(v) && v != serial && v != status);
                if (serial is null && designation is null && status is null)
                {
                    issues.Add(new ImportIssue(ws.Name, row.RowNumber(), "Warning", "\u0421\u0442\u0440\u043E\u043A\u0430 \u043D\u0435 \u0440\u0430\u0441\u043F\u043E\u0437\u043D\u0430\u043D\u0430 \u043A\u0430\u043A \u0438\u0437\u0434\u0435\u043B\u0438\u0435 \u0438\u043B\u0438 \u0432\u0445\u043E\u0434\u044F\u0449\u0438\u0439 \u044D\u043B\u0435\u043C\u0435\u043D\u0442"));
                    continue;
                }
                var confidence = serial is not null && status is not null ? RecognitionConfidence.High : RecognitionConfidence.Low;
                if (confidence == RecognitionConfidence.Low) issues.Add(new ImportIssue(ws.Name, row.RowNumber(), "Warning", "\u041D\u0435\u0434\u043E\u0441\u0442\u0430\u0442\u043E\u0447\u043D\u043E \u043F\u0440\u0438\u0437\u043D\u0430\u043A\u043E\u0432 \u0434\u043B\u044F \u0443\u0432\u0435\u0440\u0435\u043D\u043D\u043E\u0433\u043E \u0440\u0430\u0441\u043F\u043E\u0437\u043D\u0430\u0432\u0430\u043D\u0438\u044F"));
                var key = TextNormalizer.StableKey(serial, null, designation, name, null);
                if (string.IsNullOrWhiteSpace(key)) key = $"{ws.Name}:{row.RowNumber()}";
                products.Add(new ProductSnapshot(key, name, designation, serial, null, null, status, null, null, ParseSheetDate(ws.Name), null, null, confidence, source));
            }
        }
        var changed = CountStatusChanges(products);
        var report = new ImportReport(importedAt, sourcePath, wb.Worksheets.Count, rows, products.Count, incoming.Count, 0, changed, issues.Count(i => i.Message.Contains("\u043D\u0435 \u0440\u0430\u0441\u043F\u043E\u0437\u043D\u0430\u043D\u0430")), issues.Count(i => i.Severity == "Warning"), issues);
        return new ImportResult(products, incoming, report);
    }

    private static bool LooksLikeHeader(string text) => TextNormalizer.Normalize(text) is var n && (n.Contains("\u0417\u0410\u0412") && n.Contains("\u041D\u041E\u041C") || n.Contains("\u041D\u0410\u0420\u042F\u0414") || n.Contains("\u0414\u041E\u0413\u041E\u0412\u041E\u0420"));
    private static string? FirstMatch(IEnumerable<string> values, Func<string, bool> predicate) => values.Select(v => v.Trim()).FirstOrDefault(v => v.Length > 0 && predicate(v));
    private static int CountStatusChanges(IEnumerable<ProductSnapshot> products) => products.GroupBy(p => p.StableKey).Count(g => g.Select(x => TextNormalizer.Normalize(x.Status)).Distinct().Count() > 1);
    private static DateTime? ParseSheetDate(string sheet) => DateTime.TryParseExact(sheet, "dd.MM", null, System.Globalization.DateTimeStyles.None, out var d) ? new DateTime(DateTime.Now.Year, d.Month, d.Day) : null;
    private static string ColumnName(int number) { var name = string.Empty; while (number > 0) { var rem = (number - 1) % 26; name = (char)('A' + rem) + name; number = (number - rem) / 26; } return name; }
}

public sealed record ImportResult(IReadOnlyList<ProductSnapshot> Products, IReadOnlyList<IncomingItem> Incoming, ImportReport Report);
