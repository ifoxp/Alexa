using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Windows.Storage.Pickers;
using AlexaSettingsWinUI.Controls;
using AlexaSettingsWinUI.Models;

namespace AlexaSettingsWinUI.Pages;

public sealed partial class GeneralPage : Page
{
    private readonly Dictionary<string, CheckBox> _langCheckboxes = [];

    public GeneralPage()
    {
        InitializeComponent();
        BuildLanguageCheckboxes();
        LoadFromConfig();
    }

    private void BuildLanguageCheckboxes()
    {
        PnlLanguages.Children.Clear();
        _langCheckboxes.Clear();

        // WrapPanel — переносить на наступний рядок якщо не вміщується
        var wrap = new WrapPanel { ItemSpacing = 4, LineSpacing = 0 };
        foreach (var kv in LanguageOptions.All)
        {
            var chk = new CheckBox
            {
                Content = kv.Value,
                Tag     = kv.Key,
                MinWidth = 0,
            };
            _langCheckboxes[kv.Key] = chk;
            wrap.Children.Add(chk);
        }
        PnlLanguages.Children.Add(wrap);
    }

    private void LoadFromConfig()
    {
        var cfg = MainWindow.Config;
        ConfigPathBar.Message = MainWindow.ConfigPath;

        TxtPicovoiceKey.Password = cfg.PicovoiceAccessKey;
        TxtOpenAiKey.Password    = cfg.OpenaiApiKey;

        RbCustom.IsChecked   = cfg.WakeWordMode == "custom";
        RbStandard.IsChecked = cfg.WakeWordMode != "custom";
        UpdateWakeWordMode();

        // Вибираємо потрібний ComboBox item
        foreach (ComboBoxItem item in CmbWakeWord.Items)
            if (item.Tag?.ToString() == cfg.WakeWordStandard)
            { CmbWakeWord.SelectedItem = item; break; }
        if (CmbWakeWord.SelectedIndex < 0) CmbWakeWord.SelectedIndex = 0;

        TxtCustomPath.Text = cfg.CustomWakeWordPath;
        SliderSensitivity.Value = cfg.Sensitivity * 100;
        TxtSensitivityVal.Text = cfg.Sensitivity.ToString("F2");

        var active = cfg.Languages.Count > 0 ? cfg.Languages : ["uk-UA", "ru-RU", "en-US"];
        foreach (var kv in _langCheckboxes)
            kv.Value.IsChecked = active.Contains(kv.Key);
    }

    private bool SaveToConfig()
    {
        var cfg = MainWindow.Config;
        cfg.PicovoiceAccessKey = TxtPicovoiceKey.Password.Trim();
        cfg.OpenaiApiKey       = TxtOpenAiKey.Password.Trim();

        cfg.WakeWordMode      = RbCustom.IsChecked == true ? "custom" : "standard";
        cfg.WakeWordStandard  = (CmbWakeWord.SelectedItem as ComboBoxItem)?.Tag?.ToString() ?? "alexa";
        cfg.CustomWakeWordPath = TxtCustomPath.Text.Trim();
        cfg.Sensitivity       = SliderSensitivity.Value / 100.0;

        cfg.Languages = _langCheckboxes
            .Where(kv => kv.Value.IsChecked == true)
            .Select(kv => kv.Key)
            .ToList();

        return cfg.Languages.Count > 0;
    }

    private void UpdateWakeWordMode()
    {
        bool isCustom = RbCustom.IsChecked == true;
        CmbWakeWord.Visibility        = isCustom ? Visibility.Collapsed : Visibility.Visible;
        CustomWakeWordGrid.Visibility = isCustom ? Visibility.Visible   : Visibility.Collapsed;
    }

    private void WakeWordMode_Changed(object sender, RoutedEventArgs e) => UpdateWakeWordMode();

    private void SliderSensitivity_ValueChanged(object sender, Microsoft.UI.Xaml.Controls.Primitives.RangeBaseValueChangedEventArgs e)
        => TxtSensitivityVal.Text = (e.NewValue / 100.0).ToString("F2");

    private async void BtnBrowse_Click(object sender, RoutedEventArgs e)
    {
        var picker = new FileOpenPicker();
        // WinUI 3 unpackaged — треба прив'язати вікно
        var hwnd = WinRT.Interop.WindowNative.GetWindowHandle(App.MainWindow);
        WinRT.Interop.InitializeWithWindow.Initialize(picker, hwnd);
        picker.FileTypeFilter.Add(".ppn");
        var file = await picker.PickSingleFileAsync();
        if (file != null) TxtCustomPath.Text = file.Path;
    }

    private async void BtnSave_Click(object sender, RoutedEventArgs e)
    {
        if (!SaveToConfig())
        {
            await ShowDialog("Потрібно обрати хоча б одну мову.");
            return;
        }
        bool ok = ConfigLoader.Save(MainWindow.ConfigPath, MainWindow.Config);
        await ShowDialog(ok ? "Налаштування збережено!" : "Помилка збереження файлу.");
    }

    private async Task ShowDialog(string message)
    {
        var dlg = new ContentDialog
        {
            Title = "Alexa Settings",
            Content = message,
            CloseButtonText = "OK",
            XamlRoot = XamlRoot
        };
        await dlg.ShowAsync();
    }
}
