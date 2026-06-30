using System.Windows;
using System.Windows.Controls;
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

    private async void Import_Click(object sender, RoutedEventArgs e) => await _vm.ImportAsync();
    private void Search_TextChanged(object sender, TextChangedEventArgs e) => ProductsGrid.ItemsSource = _vm.FilteredProducts();
}
