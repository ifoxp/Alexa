using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Media;
using NAudio.CoreAudioApi;
using NAudio.Wave;
using AlexaSettingsWinUI.Models;

namespace AlexaSettingsWinUI.Pages;

public sealed partial class AudioPage : Page
{
    private WaveInEvent?  _micCapture;
    private DispatcherTimer? _micTimer;
    private float _micLevel;
    private bool  _micRunning;

    public AudioPage()
    {
        InitializeComponent();
        LoadMicrophones();
        LoadVoices();
        LoadFromConfig();
    }

    private void LoadMicrophones()
    {
        CmbMicrophone.Items.Clear();
        CmbMicrophone.Items.Add("(За замовчуванням системи)");
        try
        {
            var devices = new MMDeviceEnumerator()
                .EnumerateAudioEndPoints(DataFlow.Capture, DeviceState.Active);
            foreach (var d in devices)
                CmbMicrophone.Items.Add(d.FriendlyName);
        }
        catch { }
        CmbMicrophone.SelectedIndex = 0;
    }

    private void LoadVoices()
    {
        CmbTtsVoice.Items.Clear();
        foreach (var kv in VoiceOptions.All)
            CmbTtsVoice.Items.Add(new ComboBoxItem { Content = kv.Value, Tag = kv.Key });
        if (CmbTtsVoice.Items.Count > 0) CmbTtsVoice.SelectedIndex = 0;
    }

    private void LoadFromConfig()
    {
        var cfg = MainWindow.Config;

        // Мікрофон
        if (!string.IsNullOrEmpty(cfg.MicrophoneDevice))
        {
            for (int i = 0; i < CmbMicrophone.Items.Count; i++)
                if (CmbMicrophone.Items[i]?.ToString() == cfg.MicrophoneDevice)
                { CmbMicrophone.SelectedIndex = i; break; }
        }

        // Гучність мікрофону — читаємо з системи
        try
        {
            var dev = new MMDeviceEnumerator().GetDefaultAudioEndpoint(DataFlow.Capture, Role.Communications);
            int vol = (int)Math.Round(dev.AudioEndpointVolume.MasterVolumeLevelScalar * 100);
            SliderMicVol.Value = cfg.MicrophoneVolume >= 0 ? cfg.MicrophoneVolume : vol;
        }
        catch { SliderMicVol.Value = 100; }
        TxtMicVolVal.Text = SliderMicVol.Value + "%";

        // TTS
        TglTtsEnabled.IsOn = cfg.TtsEnabled;
        TxtTtsRate.Text    = cfg.TtsRate;
        foreach (ComboBoxItem item in CmbTtsVoice.Items)
            if (item.Tag?.ToString() == cfg.TtsVoice)
            { CmbTtsVoice.SelectedItem = item; break; }

        TglGeminiSTT.IsOn = cfg.UseGeminiSTT;
    }

    private void SaveToConfig()
    {
        var cfg = MainWindow.Config;

        cfg.MicrophoneDevice = CmbMicrophone.SelectedIndex <= 0
            ? "" : CmbMicrophone.SelectedItem?.ToString() ?? "";
        cfg.MicrophoneVolume = (int)SliderMicVol.Value;
        SetMicVolume((int)SliderMicVol.Value);

        cfg.TtsEnabled = TglTtsEnabled.IsOn;
        cfg.TtsRate    = TxtTtsRate.Text.Trim();
        cfg.TtsVoice   = (CmbTtsVoice.SelectedItem as ComboBoxItem)?.Tag?.ToString() ?? "jarvis";
        cfg.UseGeminiSTT = TglGeminiSTT.IsOn;
    }

    private void SetMicVolume(int percent)
    {
        try
        {
            string? selected = CmbMicrophone.SelectedIndex > 0 ? CmbMicrophone.SelectedItem?.ToString() : null;
            var enumerator = new MMDeviceEnumerator();
            MMDevice? dev = null;
            if (!string.IsNullOrEmpty(selected))
            {
                var all = enumerator.EnumerateAudioEndPoints(DataFlow.Capture, DeviceState.Active);
                dev = all.FirstOrDefault(d => d.FriendlyName == selected);
            }
            dev ??= enumerator.GetDefaultAudioEndpoint(DataFlow.Capture, Role.Communications);
            dev.AudioEndpointVolume.MasterVolumeLevelScalar = percent / 100f;
        }
        catch { }
    }

    private void SliderMicVol_ValueChanged(object sender, Microsoft.UI.Xaml.Controls.Primitives.RangeBaseValueChangedEventArgs e)
        => TxtMicVolVal.Text = ((int)e.NewValue) + "%";

    private void BtnMicTest_Click(object sender, RoutedEventArgs e)
    {
        if (_micRunning) StopMicTest();
        else             StartMicTest();
    }

    private void StartMicTest()
    {
        try
        {
            int deviceIdx = 0;
            string? selected = CmbMicrophone.SelectedIndex > 0 ? CmbMicrophone.SelectedItem?.ToString() : null;
            if (!string.IsNullOrEmpty(selected))
                for (int i = 0; i < WaveIn.DeviceCount; i++)
                {
                    var caps = WaveIn.GetCapabilities(i);
                    if (caps.ProductName.Contains(selected[..Math.Min(31, selected.Length)], StringComparison.OrdinalIgnoreCase))
                    { deviceIdx = i; break; }
                }

            _micCapture = new WaveInEvent
            {
                DeviceNumber = deviceIdx,
                WaveFormat   = new WaveFormat(16000, 16, 1),
                BufferMilliseconds = 50
            };
            _micCapture.DataAvailable += (s, a) =>
            {
                float sum = 0; int count = a.BytesRecorded / 2;
                for (int i = 0; i < a.BytesRecorded - 1; i += 2)
                {
                    short sample = BitConverter.ToInt16(a.Buffer, i);
                    float n = sample / 32768f;
                    sum += n * n;
                }
                _micLevel = Math.Min((float)Math.Sqrt(sum / Math.Max(count, 1)) * 5f, 1f);
            };
            _micCapture.StartRecording();

            _micTimer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(50) };
            _micTimer.Tick += (s, e) =>
            {
                int level = (int)(_micLevel * 100);
                PbMicLevel.Value = Math.Clamp(level, 0, 100);
                PbMicLevel.Foreground = level > 80
                    ? new SolidColorBrush(Windows.UI.Color.FromArgb(255, 200, 50, 50))
                    : level > 50
                        ? new SolidColorBrush(Windows.UI.Color.FromArgb(255, 220, 160, 0))
                        : new SolidColorBrush(Windows.UI.Color.FromArgb(255, 37, 150, 90));
            };
            _micTimer.Start();
            _micRunning = true;
            BtnMicTest.Content = "⏹ Зупинити тест";
        }
        catch (Exception ex)
        {
            _ = ShowDialog($"Помилка запуску тесту:\n{ex.Message}");
        }
    }

    private void StopMicTest()
    {
        _micRunning = false;
        _micTimer?.Stop();
        _micTimer = null;
        _micCapture?.StopRecording();
        _micCapture?.Dispose();
        _micCapture = null;
        PbMicLevel.Value = 0;
        BtnMicTest.Content = "▶ Почати тест мікрофону";
    }

    private async void BtnSave_Click(object sender, RoutedEventArgs e)
    {
        SaveToConfig();
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
