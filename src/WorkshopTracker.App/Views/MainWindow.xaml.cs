using System.IO;
using Microsoft.Win32;
using System.Windows;
using WorkshopTracker.App.ViewModels;

namespace WorkshopTracker.App.Views;

public partial class MainWindow : Window
{
    private readonly MainViewModel _vm = new();
    public MainWindow()
    {
        InitializeComponent();
        DataContext = _vm;
    }

    private void Browse_Click(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFileDialog
        {
            Title = "\u0412\u044B\u0431\u0435\u0440\u0438\u0442\u0435 Excel-\u0444\u0430\u0439\u043B \u043E\u0442\u0441\u043B\u0435\u0436\u0438\u0432\u0430\u043D\u0438\u044F",
            Filter = "Excel workbook (*.xlsx)|*.xlsx",
            CheckFileExists = true,
            Multiselect = false,
            InitialDirectory = GetInitialDirectory()
        };

        if (dialog.ShowDialog(this) == true)
            _vm.ExcelPath = dialog.FileName;
    }

    private async void Import_Click(object sender, RoutedEventArgs e)
    {
        await _vm.ImportAsync();
        MessageBox.Show(_vm.Status, "\u0418\u043C\u043F\u043E\u0440\u0442 Excel", MessageBoxButton.OK, MessageBoxImage.Information);
    }

    private static string GetInitialDirectory()
    {
        var downloads = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Downloads");
        return Directory.Exists(downloads) ? downloads : Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
    }
}
