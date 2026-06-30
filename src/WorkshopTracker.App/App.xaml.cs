using System.Windows;
using System.Windows.Threading;

namespace WorkshopTracker.App;

public partial class App : Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        DispatcherUnhandledException += OnDispatcherUnhandledException;
        AppDomain.CurrentDomain.UnhandledException += OnUnhandledException;
        base.OnStartup(e);
    }

    private static void OnDispatcherUnhandledException(object sender, DispatcherUnhandledExceptionEventArgs e)
    {
        MessageBox.Show($"Приложение не смогло выполнить действие.\n\n{e.Exception.Message}", "Ошибка", MessageBoxButton.OK, MessageBoxImage.Error);
        e.Handled = true;
    }

    private static void OnUnhandledException(object sender, UnhandledExceptionEventArgs e)
    {
        if (e.ExceptionObject is Exception ex)
            MessageBox.Show($"Критическая ошибка приложения.\n\n{ex.Message}", "Ошибка", MessageBoxButton.OK, MessageBoxImage.Error);
    }
}
