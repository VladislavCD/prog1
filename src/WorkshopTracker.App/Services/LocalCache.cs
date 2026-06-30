using System.IO;
using Microsoft.Data.Sqlite;
using WorkshopTracker.App.Models;

namespace WorkshopTracker.App.Services;

public sealed class LocalCache
{
    private readonly string _dbPath;
    public LocalCache(string dbPath) => _dbPath = dbPath;
    public string DbPath => _dbPath;

    public async Task InitializeAsync()
    {
        Directory.CreateDirectory(Path.GetDirectoryName(_dbPath)!);
        await using var db = new SqliteConnection($"Data Source={_dbPath}");
        await db.OpenAsync();
        var sql = """
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS product_snapshots(
          id INTEGER PRIMARY KEY, stable_key TEXT NOT NULL, name TEXT, designation TEXT, serial_number TEXT,
          work_order TEXT, contract TEXT, status TEXT, operation TEXT, next_operation TEXT, status_date TEXT,
          note TEXT, planned_date TEXT, confidence TEXT NOT NULL, file_name TEXT NOT NULL, sheet_name TEXT NOT NULL,
          row_number INTEGER NOT NULL, cell_range TEXT NOT NULL, imported_at TEXT NOT NULL);
        CREATE INDEX IF NOT EXISTS ix_product_key_sheet ON product_snapshots(stable_key, sheet_name);
        CREATE VIRTUAL TABLE IF NOT EXISTS product_fts USING fts5(stable_key, name, designation, serial_number, work_order, contract, status, operation, note, content='');
        CREATE TABLE IF NOT EXISTS incoming_items(id INTEGER PRIMARY KEY, product_key TEXT NOT NULL, name TEXT NOT NULL, designation TEXT, serial_number TEXT, status TEXT, note TEXT, level INTEGER, file_name TEXT, sheet_name TEXT, row_number INTEGER, cell_range TEXT, imported_at TEXT);
        CREATE TABLE IF NOT EXISTS import_logs(id INTEGER PRIMARY KEY, imported_at TEXT, excel_path TEXT, sheets_read INTEGER, rows_processed INTEGER, products_recognized INTEGER, incoming_recognized INTEGER, new_products INTEGER, changed_products INTEGER, unrecognized_rows INTEGER, rows_need_review INTEGER, errors INTEGER, warnings INTEGER);
        CREATE TABLE IF NOT EXISTS import_issues(id INTEGER PRIMARY KEY, imported_at TEXT, sheet_name TEXT, row_number INTEGER, severity TEXT, message TEXT);
        """;
        await new SqliteCommand(sql, db).ExecuteNonQueryAsync();
    }

    public void BackupIfExists()
    {
        if (!File.Exists(_dbPath)) return;
        var backup = Path.Combine(Path.GetDirectoryName(_dbPath)!, $"cache-{DateTime.Now:yyyyMMdd-HHmmss}.bak.sqlite");
        File.Copy(_dbPath, backup, overwrite: false);
    }

    public async Task ReplaceSnapshotsAsync(IEnumerable<ProductSnapshot> products, IEnumerable<IncomingItem> incoming, ImportReport report)
    {
        await using var db = new SqliteConnection($"Data Source={_dbPath}");
        await db.OpenAsync();
        await using var tx = await db.BeginTransactionAsync();
        foreach (var stmt in new[] { "DELETE FROM product_snapshots", "DELETE FROM product_fts", "DELETE FROM incoming_items" })
            await new SqliteCommand(stmt, db, (SqliteTransaction)tx).ExecuteNonQueryAsync();
        foreach (var p in products)
        {
            var cmd = db.CreateCommand(); cmd.Transaction = (SqliteTransaction)tx;
            cmd.CommandText = "INSERT INTO product_snapshots(stable_key,name,designation,serial_number,work_order,contract,status,operation,next_operation,status_date,note,planned_date,confidence,file_name,sheet_name,row_number,cell_range,imported_at) VALUES($k,$n,$d,$s,$w,$c,$st,$o,$no,$sd,$note,$pd,$conf,$f,$sh,$r,$cr,$ia); INSERT INTO product_fts(stable_key,name,designation,serial_number,work_order,contract,status,operation,note) VALUES($k,$n,$d,$s,$w,$c,$st,$o,$note);";
            Add(cmd, "$k", p.StableKey); Add(cmd, "$n", p.Name); Add(cmd, "$d", p.Designation); Add(cmd, "$s", p.SerialNumber); Add(cmd, "$w", p.WorkOrder); Add(cmd, "$c", p.Contract); Add(cmd, "$st", p.Status); Add(cmd, "$o", p.Operation); Add(cmd, "$no", p.NextOperation); Add(cmd, "$sd", p.StatusDate?.ToString("O")); Add(cmd, "$note", p.Note); Add(cmd, "$pd", p.PlannedDate?.ToString("O")); Add(cmd, "$conf", p.Confidence.ToString()); Add(cmd, "$f", p.Source.FileName); Add(cmd, "$sh", p.Source.SheetName); Add(cmd, "$r", p.Source.RowNumber); Add(cmd, "$cr", p.Source.CellRange); Add(cmd, "$ia", p.Source.ImportedAt.ToString("O"));
            await cmd.ExecuteNonQueryAsync();
        }
        foreach (var i in incoming)
        {
            var cmd = db.CreateCommand(); cmd.Transaction = (SqliteTransaction)tx;
            cmd.CommandText = "INSERT INTO incoming_items(product_key,name,designation,serial_number,status,note,level,file_name,sheet_name,row_number,cell_range,imported_at) VALUES($k,$n,$d,$s,$st,$note,$l,$f,$sh,$r,$cr,$ia)";
            Add(cmd,"$k",i.ProductKey); Add(cmd,"$n",i.Name); Add(cmd,"$d",i.Designation); Add(cmd,"$s",i.SerialNumber); Add(cmd,"$st",i.Status); Add(cmd,"$note",i.Note); Add(cmd,"$l",i.Level); Add(cmd,"$f",i.Source.FileName); Add(cmd,"$sh",i.Source.SheetName); Add(cmd,"$r",i.Source.RowNumber); Add(cmd,"$cr",i.Source.CellRange); Add(cmd,"$ia",i.Source.ImportedAt.ToString("O"));
            await cmd.ExecuteNonQueryAsync();
        }
        await SaveReportAsync(db, (SqliteTransaction)tx, report);
        await tx.CommitAsync();
    }

    private static async Task SaveReportAsync(SqliteConnection db, SqliteTransaction tx, ImportReport r)
    {
        var cmd = db.CreateCommand(); cmd.Transaction = tx;
        cmd.CommandText = "INSERT INTO import_logs(imported_at,excel_path,sheets_read,rows_processed,products_recognized,incoming_recognized,new_products,changed_products,unrecognized_rows,rows_need_review,errors,warnings) VALUES($i,$p,$s,$rp,$pr,$ir,$n,$c,$u,$rev,$e,$w)";
        Add(cmd,"$i",r.ImportedAt.ToString("O")); Add(cmd,"$p",r.ExcelPath); Add(cmd,"$s",r.SheetsRead); Add(cmd,"$rp",r.RowsProcessed); Add(cmd,"$pr",r.ProductsRecognized); Add(cmd,"$ir",r.IncomingRecognized); Add(cmd,"$n",r.NewProducts); Add(cmd,"$c",r.ChangedProducts); Add(cmd,"$u",r.UnrecognizedRows); Add(cmd,"$rev",r.RowsNeedReview); Add(cmd,"$e",r.Issues.Count(x=>x.Severity=="Error")); Add(cmd,"$w",r.Issues.Count(x=>x.Severity!="Error"));
        await cmd.ExecuteNonQueryAsync();
    }
    private static void Add(SqliteCommand cmd, string name, object? value) => cmd.Parameters.AddWithValue(name, value ?? DBNull.Value);
}
