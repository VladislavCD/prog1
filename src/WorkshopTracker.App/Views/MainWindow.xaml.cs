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
            Title = "Выберите Excel-файл отслеживания",
            Filter = "Excel workbook (*.xlsx)|*.xlsx",
            CheckFileExists = true,
            Multiselect = false,
            InitialDirectory = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile)
        };

        if (dialog.ShowDialog(this) == true)
            _vm.ExcelPath = dialog.FileName;
    }

    private async void Import_Click(object sender, RoutedEventArgs e) => await _vm.ImportAsync();
}
