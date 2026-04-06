using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using AlexaSettingsWinUI.Models;

namespace AlexaSettingsWinUI.Pages;

public sealed partial class AdvancedPage : Page
{
    public AdvancedPage()
    {
        InitializeComponent();
        LoadFromConfig();
    }

    private void LoadFromConfig()
    {
        var cfg = MainWindow.Config;
        TxtRoutingModel.Text      = cfg.RoutingModel;
        TxtPluginModel.Text       = cfg.PluginModel;
        NudCommandTimeout.Value   = cfg.CommandSessionTimeout;
        NudContinuousListen.Value = cfg.ContinuousListenSeconds;
        NudSilenceDetect.Value    = cfg.SilenceDetectSeconds;
        NudSilenceTimeout.Value   = cfg.SilenceTimeout;
    }

    private void SaveToConfig()
    {
        var cfg = MainWindow.Config;
        cfg.RoutingModel           = TxtRoutingModel.Text.Trim();
        cfg.PluginModel            = TxtPluginModel.Text.Trim();
        cfg.CommandSessionTimeout  = (int)NudCommandTimeout.Value;
        cfg.ContinuousListenSeconds = (int)NudContinuousListen.Value;
        cfg.SilenceDetectSeconds   = NudSilenceDetect.Value;
        cfg.SilenceTimeout         = NudSilenceTimeout.Value;
    }

    private async void BtnSave_Click(object sender, RoutedEventArgs e)
    {
        SaveToConfig();
        bool ok = ConfigLoader.Save(MainWindow.ConfigPath, MainWindow.Config);
        var dlg = new ContentDialog
        {
            Title = "Alexa Settings",
            Content = ok ? "Налаштування збережено!" : "Помилка збереження.",
            CloseButtonText = "OK",
            XamlRoot = XamlRoot
        };
        await dlg.ShowAsync();
    }
}
