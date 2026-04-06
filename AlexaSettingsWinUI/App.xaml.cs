using Microsoft.UI.Xaml;

namespace AlexaSettingsWinUI;

public partial class App : Application
{
    public static MainWindow? MainWindow { get; private set; }

    public App()
    {
        this.UnhandledException += (s, e) =>
        {
            File.WriteAllText("C:\\Temp\\alexa_xaml_crash.txt",
                $"{e.Exception?.GetType()}\n{e.Exception?.Message}\n{e.Exception?.StackTrace}");
            e.Handled = true;
        };
        InitializeComponent();
    }

    protected override void OnLaunched(LaunchActivatedEventArgs args)
    {
        MainWindow = new MainWindow();
        MainWindow.Activate();
    }
}
