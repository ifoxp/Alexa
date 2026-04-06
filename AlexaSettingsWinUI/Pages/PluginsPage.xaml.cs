using Microsoft.UI;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using AlexaSettingsWinUI.Controls;
using AlexaSettingsWinUI.Models;

namespace AlexaSettingsWinUI.Pages;

public sealed partial class PluginsPage : Page
{
    private readonly Dictionary<string, ToggleSwitch> _toggles = [];

    public PluginsPage()
    {
        InitializeComponent();
        BuildPluginCards();
    }

    private void BuildPluginCards()
    {
        PluginsList.Items.Clear();
        _toggles.Clear();

        var plugins = PluginParser.LoadAll();
        TxtPluginsDir.Text = "Папка: " + PluginParser.FindPluginsDir();

        if (plugins.Count == 0)
        {
            PluginsList.Items.Add(new InfoBar
            {
                IsOpen    = true,
                IsClosable = false,
                Severity  = InfoBarSeverity.Warning,
                Title     = "Плагіни не знайдені",
                Message   = "Запустіть після білду, коли папка plugins/ буде поряд з .exe",
            });
            return;
        }

        var disabled = MainWindow.Config.DisabledPlugins;

        foreach (var info in plugins)
        {
            var card = BuildCard(info, !disabled.Contains(info.PluginName));
            PluginsList.Items.Add(card);
        }
    }

    private Border BuildCard(PluginInfo info, bool enabled)
    {
        // ToggleSwitch для ввімкнення плагіна
        var toggle = new ToggleSwitch
        {
            IsOn       = enabled,
            OnContent  = "",
            OffContent = "",
            Margin     = new Thickness(0),
        };
        _toggles[info.PluginName] = toggle;

        // Назва + toggle в один рядок
        var header = new Grid();
        header.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
        header.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

        var nameBlock = new TextBlock
        {
            Text       = info.PluginName,
            Style      = Application.Current.Resources["BodyStrongTextBlockStyle"] as Style,
            VerticalAlignment = VerticalAlignment.Center,
        };
        Grid.SetColumn(nameBlock, 0);
        Grid.SetColumn(toggle, 1);
        header.Children.Add(nameBlock);
        header.Children.Add(toggle);

        // Опис
        var desc = new TextBlock
        {
            Text       = info.Description,
            TextWrapping = TextWrapping.WrapWholeWords,
            Foreground = Application.Current.Resources["TextFillColorSecondaryBrush"] as Brush,
            Margin     = new Thickness(0, 4, 0, 6),
            FontSize   = 12,
        };

        // Команди — кожна на своєму рядку: бейдж + опис
        var cmdsPanel = new StackPanel { Spacing = 6, Margin = new Thickness(0, 8, 0, 0) };

        // Розділювач
        cmdsPanel.Children.Add(new Border
        {
            Height = 1,
            Background = Application.Current.Resources["DividerStrokeColorDefaultBrush"] as Brush,
            Margin = new Thickness(0, 0, 0, 4),
        });

        foreach (var cmd in info.Commands)
        {
            var row = new Grid { ColumnSpacing = 10 };
            row.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

            var badge = new Border
            {
                Background   = Application.Current.Resources["AccentFillColorDefaultBrush"] as Brush,
                CornerRadius = new CornerRadius(4),
                Padding      = new Thickness(8, 2, 8, 2),
                VerticalAlignment = VerticalAlignment.Top,
                Child = new TextBlock
                {
                    Text      = cmd.Key,
                    FontSize  = 11,
                    Foreground = new SolidColorBrush(Colors.White),
                }
            };

            var cmdDesc = new TextBlock
            {
                Text         = cmd.Value,
                FontSize     = 12,
                TextWrapping = TextWrapping.WrapWholeWords,
                Foreground   = Application.Current.Resources["TextFillColorSecondaryBrush"] as Brush,
                VerticalAlignment = VerticalAlignment.Top,
            };

            Grid.SetColumn(badge, 0);
            Grid.SetColumn(cmdDesc, 1);
            row.Children.Add(badge);
            row.Children.Add(cmdDesc);
            cmdsPanel.Children.Add(row);
        }

        // Складаємо картку
        var content = new StackPanel { Spacing = 0 };
        content.Children.Add(header);
        content.Children.Add(desc);
        content.Children.Add(cmdsPanel);

        return new Border
        {
            Child         = content,
            Padding       = new Thickness(16, 12, 16, 12),
            Margin        = new Thickness(0, 0, 0, 8),
            CornerRadius  = new CornerRadius(8),
            Background    = Application.Current.Resources["CardBackgroundFillColorDefaultBrush"] as Brush,
            BorderBrush   = Application.Current.Resources["CardStrokeColorDefaultBrush"] as Brush,
            BorderThickness = new Thickness(1),
        };
    }

    private async void BtnSave_Click(object sender, RoutedEventArgs e)
    {
        MainWindow.Config.DisabledPlugins = _toggles
            .Where(kv => !kv.Value.IsOn)
            .Select(kv => kv.Key)
            .ToList();

        bool ok = ConfigLoader.Save(MainWindow.ConfigPath, MainWindow.Config);
        var dlg = new ContentDialog
        {
            Title = "Alexa Settings",
            Content = ok ? "Налаштування збережено!" : "Помилка збереження файлу.",
            CloseButtonText = "OK",
            XamlRoot = XamlRoot
        };
        await dlg.ShowAsync();
    }
}

