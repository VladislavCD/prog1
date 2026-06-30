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
assert 'File.Copy(excelPath, temp' in importer
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
print('static checks passed')
