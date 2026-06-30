from pathlib import Path

root = Path(__file__).resolve().parents[1]
required = [
    root / 'WorkshopTracker.sln',
    root / 'src/WorkshopTracker.App/WorkshopTracker.App.csproj',
    root / 'src/WorkshopTracker.App/Services/ExcelImportService.cs',
    root / 'src/WorkshopTracker.App/Services/LocalCache.cs',
    root / 'src/WorkshopTracker.App/Views/MainWindow.xaml',
    root / 'src/WorkshopTracker.App/Views/MainWindow.xaml.cs',
]
missing = [str(p.relative_to(root)) for p in required if not p.exists()]
assert not missing, f'Missing files: {missing}'
csproj = (root / 'src/WorkshopTracker.App/WorkshopTracker.App.csproj').read_text(encoding='utf-8')
assert 'net8.0-windows' in csproj
assert '<CodePage>65001</CodePage>' in csproj
assert 'ClosedXML' in csproj
assert 'Microsoft.Data.Sqlite' in csproj
importer = (root / 'src/WorkshopTracker.App/Services/ExcelImportService.cs').read_text(encoding='utf-8')
assert 'CopyWorkbookToTempAsync(excelPath, temp' in importer
assert 'Path.Combine(workingDirectory, "temp")' in importer
assert 'FileShare.ReadWrite | FileShare.Delete' in importer
assert 'File.SetAttributes(tempPath, File.GetAttributes(tempPath) | FileAttributes.ReadOnly)' in importer
assert 'new FileStream(tempPath, FileMode.Open, FileAccess.Read, FileShare.Read)' in importer
assert 'File.Delete(temp)' in importer
cache = (root / 'src/WorkshopTracker.App/Services/LocalCache.cs').read_text(encoding='utf-8')
assert 'CREATE VIRTUAL TABLE IF NOT EXISTS product_fts USING fts5' in cache
assert 'BackupIfExists' in cache
xaml = (root / 'src/WorkshopTracker.App/Views/MainWindow.xaml').read_text(encoding='utf-8')
assert 'Выбрать файл' in xaml
assert 'Поиск по загруженным данным' in xaml
codebehind = (root / 'src/WorkshopTracker.App/Views/MainWindow.xaml.cs').read_text(encoding='utf-8')
assert 'OpenFileDialog' in codebehind
assert 'MessageBox.Show(_vm.Status' in codebehind
vm = (root / 'src/WorkshopTracker.App/ViewModels/MainViewModel.cs').read_text(encoding='utf-8')
assert 'GetWritableAppDataDirectory' in vm
assert 'WorkshopTrackerData' in vm
assert 'Path.Combine(_dataDirectory, "logs")' in vm
assert 'import.log' in vm
assert '_importer.ImportAsync(ExcelPath, _dataDirectory)' in vm
assert '\\u041D\\u0435 \\u0443\\u0434\\u0430\\u043B\\u043E\\u0441\\u044C' in vm
assert '\\u041A\\u043D\\u0438\\u0433\\u0430 \\u0441 \\u043F\\u0430\\u0440\\u043E\\u043B\\u0435\\u043C' in vm
readme = (root / 'README.md').read_text(encoding='utf-8')
assert 'паролем **на запись/изменение** поддерживаются' in readme
assert 'WorkshopTrackerData' in readme
assert 'не сохраняются в `C:\\Windows`' in readme
for cs in (root / 'src/WorkshopTracker.App').rglob('*.cs'):
    content = cs.read_text(encoding='utf-8')
    assert all(ord(ch) < 128 for ch in content), f'Non-ASCII text remains in {cs}'
print('static checks passed')
