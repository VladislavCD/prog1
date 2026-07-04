namespace WorkshopTracker.App.Models;

public enum RecognitionConfidence { High, Medium, Low, Unrecognized }
public enum ChangeKind { New, StatusChanged, MissingFromLatest, NoMovement, NeedsReview }

public sealed record ExcelSourceRef(string FileName, string SheetName, int RowNumber, string CellRange, DateTime ImportedAt);

public sealed record ProductSnapshot(
    string StableKey,
    string? Name,
    string? Designation,
    string? SerialNumber,
    string? WorkOrder,
    string? Contract,
    string? Status,
    string? Operation,
    string? NextOperation,
    DateTime? StatusDate,
    string? Note,
    DateTime? PlannedDate,
    RecognitionConfidence Confidence,
    ExcelSourceRef Source);

public sealed record IncomingItem(
    string ProductKey,
    string Name,
    string? Designation,
    string? SerialNumber,
    string? Status,
    string? Note,
    int Level,
    ExcelSourceRef Source);

public sealed record ImportIssue(string SheetName, int RowNumber, string Severity, string Message);

public sealed record ImportReport(
    DateTime ImportedAt,
    string ExcelPath,
    int SheetsRead,
    int RowsProcessed,
    int ProductsRecognized,
    int IncomingRecognized,
    int NewProducts,
    int ChangedProducts,
    int UnrecognizedRows,
    int RowsNeedReview,
    IReadOnlyList<ImportIssue> Issues);

public sealed record ProductChange(ChangeKind Kind, string StableKey, string? BeforeStatus, string? AfterStatus, string Description);
