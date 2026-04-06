using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using AlexaSettingsWinUI.Models;
using AlexaSettingsWinUI.Pages;

namespace AlexaSettingsWinUI;

public sealed partial class MainWindow : Window
{
    public static ConfigModel Config { get; private set; } = new();
    public static string ConfigPath { get; private set; } = "";

    public MainWindow()
    {
        InitializeComponent();

        SystemBackdrop = new MicaBackdrop();
        ExtendsContentIntoTitleBar = true;
        SetTitleBar(TitleBar);

        Title = "Alexa — Налаштування";

        ConfigPath = ConfigLocator.Find();
        Config = ConfigLoader.Load(ConfigPath);

        Activated += MainWindow_Activated;
    }

    private bool _navigated = false;
    private void MainWindow_Activated(object sender, WindowActivatedEventArgs args)
    {
        if (_navigated) return;
        _navigated = true;
        NavView.SelectedItem = NavView.MenuItems[0];
    }

    private void NavView_SelectionChanged(NavigationView sender, NavigationViewSelectionChangedEventArgs args)
    {
        if (args.SelectedItem is not NavigationViewItem item) return;

        Type? page = item.Tag?.ToString() switch
        {
            "General"   => typeof(GeneralPage),
            "Audio"     => typeof(AudioPage),
            "Plugins"   => typeof(PluginsPage),
            "Advanced"  => typeof(AdvancedPage),
            "Autostart" => typeof(AutostartPage),
            _           => null
        };

        if (page != null)
            ContentFrame.Navigate(page);
    }
}
