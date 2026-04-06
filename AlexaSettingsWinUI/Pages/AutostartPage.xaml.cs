using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.Win32;
using Windows.Storage.Pickers;

namespace AlexaSettingsWinUI.Pages;

public sealed partial class AutostartPage : Page
{
    private const string RegKey     = @"SOFTWARE\Microsoft\Windows\CurrentVersion\Run";
    private const string AppName    = "AlexaAssistant";
    private bool _suppressToggle;

    public AutostartPage()
    {
        InitializeComponent();
        LoadState();
    }

    private static string? FindAlexaExe()
    {
        string dir = AppDomain.CurrentDomain.BaseDirectory;
        string candidate = Path.Combine(dir, "Alexa.exe");
        if (File.Exists(candidate)) return candidate;

        string? parent = Path.GetDirectoryName(dir);
        if (parent != null)
        {
            candidate = Path.Combine(parent, "Alexa", "Alexa.exe");
            if (File.Exists(candidate)) return candidate;
        }
        return null;
    }

    private void LoadState()
    {
        string? alexaExe = FindAlexaExe();
        AlexaPathLabel.Text = alexaExe ?? "Alexa.exe не знайдено — запустіть після білду";

        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(RegKey, false);
            string? val = key?.GetValue(AppName) as string;
            _suppressToggle = true;
            TglAutostart.IsOn = !string.IsNullOrEmpty(val);
            _suppressToggle = false;
        }
        catch { }
    }

    private async void TglAutostart_Toggled(object sender, RoutedEventArgs e)
    {
        if (_suppressToggle) return;

        if (TglAutostart.IsOn)
        {
            string? alexaExe = FindAlexaExe();

            if (alexaExe == null)
            {
                // Пропонуємо вибрати вручну
                var picker = new FileOpenPicker();
                var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(App.MainWindow);
                WinRT.Interop.InitializeWithWindow.Initialize(picker, hwnd);
                picker.FileTypeFilter.Add(".exe");
                var file = await picker.PickSingleFileAsync();

                if (file == null)
                {
                    _suppressToggle = true;
                    TglAutostart.IsOn = false;
                    _suppressToggle = false;
                    return;
                }
                alexaExe = file.Path;
            }

            try
            {
                using var key = Registry.CurrentUser.OpenSubKey(RegKey, true);
                key?.SetValue(AppName, $"\"{alexaExe}\"");
                AlexaPathLabel.Text = alexaExe;
            }
            catch (Exception ex) { await ShowDialog($"Помилка: {ex.Message}"); }
        }
        else
        {
            try
            {
                using var key = Registry.CurrentUser.OpenSubKey(RegKey, true);
                key?.DeleteValue(AppName, throwOnMissingValue: false);
            }
            catch (Exception ex) { await ShowDialog($"Помилка: {ex.Message}"); }
        }
    }

    private async Task ShowDialog(string msg)
    {
        var dlg = new ContentDialog
        {
            Title = "Alexa Settings",
            Content = msg,
            CloseButtonText = "OK",
            XamlRoot = XamlRoot
        };
        await dlg.ShowAsync();
    }
}
