using Microsoft.Win32;
using NAudio.CoreAudioApi;
using NAudio.Wave;
using Newtonsoft.Json;

namespace AlexaSettings
{
    public partial class MainForm : Form
    {
        private string _configPath;
        private ConfigModel _config = new();

        // Чекбокси мов — будуємо динамічно
        private readonly Dictionary<string, CheckBox> _langCheckboxes = new();

        // Чекбокси плагінів — будуємо динамічно
        private readonly Dictionary<string, CheckBox> _pluginCheckboxes = new();

        // Підказки для бейджів команд
        private readonly ToolTip toolTip = new();

        // Ключ реєстру для автозапуску
        private const string AutostartRegKey = @"SOFTWARE\Microsoft\Windows\CurrentVersion\Run";
        private const string AutostartAppName = "AlexaAssistant";

        // VU-метр
        private WaveInEvent? _micTestCapture;
        private System.Windows.Forms.Timer? _micTestTimer;
        private float _currentMicLevel;
        private bool _micTestRunning;

        public MainForm()
        {
            InitializeComponent();
            _configPath = FindConfigPath();
            lblConfigPath.Text = "config.json: " + _configPath;

            InitVoiceCombo();
            BuildLanguageCheckboxes();
            BuildPluginsTab();
            LoadMicrophones();
            LoadConfig();
            LoadAutostartState();
        }

        // ─── Ініціалізація ────────────────────────────────────────

        private static string FindConfigPath()
        {
            string dir = AppDomain.CurrentDomain.BaseDirectory;
            for (int i = 0; i < 6; i++)
            {
                string candidate = Path.Combine(dir, "config.json");
                if (File.Exists(candidate)) return candidate;
                dir = Path.GetDirectoryName(dir) ?? dir;
            }
            return @"E:\Programing\Phyton\Alexa\config.json";
        }

        private void InitVoiceCombo()
        {
            cmbTtsVoice.Items.Clear();
            // Додаємо нормальні людські назви — ключ зберігається у Tag
            foreach (var kv in VoiceOptions.All)
            {
                var item = new VoiceComboItem(kv.Key, kv.Value);
                cmbTtsVoice.Items.Add(item);
            }
            cmbTtsVoice.DisplayMember = "DisplayName";
            if (cmbTtsVoice.Items.Count > 0)
                cmbTtsVoice.SelectedIndex = 0;
        }

        /// <summary>Будує чекбокси мов у pnlLanguages з усіх доступних мов.</summary>
        private void BuildLanguageCheckboxes()
        {
            pnlLanguages.Controls.Clear();
            _langCheckboxes.Clear();

            foreach (var kv in LanguageOptions.All)
            {
                var chk = new CheckBox
                {
                    Text = kv.Value,          // "Українська", "English (США)"...
                    Tag  = kv.Key,            // "uk-UA", "en-US"...
                    AutoSize = true,
                    Margin = new Padding(0, 4, 20, 4),
                    Font = new Font("Segoe UI", 9.5f)
                };
                _langCheckboxes[kv.Key] = chk;
                pnlLanguages.Controls.Add(chk);
            }
        }

        /// <summary>Будує вкладку Плагіни — читає дані прямо з .py файлів.</summary>
        private void BuildPluginsTab()
        {
            pnlPlugins.Controls.Clear();
            _pluginCheckboxes.Clear();

            var plugins = PluginParser.LoadAll();

            if (plugins.Count == 0)
            {
                var lbl = new Label
                {
                    Text = "Папку plugins/ не знайдено поруч з AlexaSettings.exe.\nЗапустіть після білду, коли plugins/ буде поряд.",
                    Location = new Point(16, 20),
                    Size = new Size(600, 40),
                    ForeColor = Color.FromArgb(180, 60, 60),
                    Font = new Font("Segoe UI", 9.5f),
                };
                pnlPlugins.Controls.Add(lbl);
                return;
            }

            Color bgEven     = Color.FromArgb(250, 250, 253);
            Color bgOdd      = Color.FromArgb(243, 245, 250);
            Color accentOn   = Color.FromArgb(37, 99, 235);
            Color descColor  = Color.FromArgb(80, 85, 100);
            Color cmdColor   = Color.FromArgb(55, 100, 170);
            Color cmdBg      = Color.FromArgb(235, 242, 255);
            int   cardWidth  = pnlPlugins.Width - 20;
            int   y          = 8;
            int   idx        = 0;

            foreach (var info in plugins)
            {
                // Обчислюємо висоту картки: 34 (header) + 20*descLines + 24*cmdCount + 8 (padding)
                int descLines = (int)Math.Ceiling(info.Description.Length / 80.0);
                int descH     = Math.Max(20, descLines * 18);
                int cardH     = 36 + descH + info.Commands.Count * 24 + 14;

                Color cardBg = (idx % 2 == 0) ? bgEven : bgOdd;

                // Картка-панель
                var card = new Panel
                {
                    Location    = new Point(8, y),
                    Size        = new Size(cardWidth, cardH),
                    BackColor   = cardBg,
                };

                // Ліва кольорова смужка
                var stripe = new Panel
                {
                    Location  = new Point(0, 0),
                    Size      = new Size(4, cardH),
                    BackColor = accentOn,
                };
                card.Controls.Add(stripe);

                // Чекбокс з назвою
                var chk = new CheckBox
                {
                    Text     = info.PluginName,
                    Tag      = info.PluginName,
                    Checked  = true,
                    AutoSize = false,
                    Width    = cardWidth - 14,
                    Height   = 26,
                    Location = new Point(12, 4),
                    Font     = new Font("Segoe UI", 10f, FontStyle.Bold),
                    ForeColor = Color.FromArgb(25, 35, 55),
                    BackColor = Color.Transparent,
                };
                chk.CheckedChanged += (s, e) =>
                {
                    stripe.BackColor = chk.Checked ? accentOn : Color.FromArgb(190, 190, 200);
                };
                _pluginCheckboxes[info.PluginName] = chk;
                card.Controls.Add(chk);

                // Опис
                int cy = 32;
                var lblDesc = new Label
                {
                    Text      = info.Description,
                    Location  = new Point(14, cy),
                    Size      = new Size(cardWidth - 22, descH),
                    ForeColor = descColor,
                    Font      = new Font("Segoe UI", 8.5f),
                    BackColor = Color.Transparent,
                };
                card.Controls.Add(lblDesc);
                cy += descH + 4;

                // Команди — бейджі
                foreach (var cmd in info.Commands)
                {
                    var badge = new Label
                    {
                        Text      = $"  {cmd.Key}  ",
                        Location  = new Point(14, cy),
                        AutoSize  = true,
                        ForeColor = cmdColor,
                        BackColor = cmdBg,
                        Font      = new Font("Segoe UI", 7.5f, FontStyle.Bold),
                        Padding   = new Padding(2, 1, 2, 1),
                        Cursor    = Cursors.Help,
                        Tag       = cmd.Value,
                    };
                    badge.MouseEnter += (s, e) =>
                    {
                        if (s is Label b) toolTip.SetToolTip(b, b.Tag?.ToString() ?? "");
                    };
                    card.Controls.Add(badge);

                    // Підказка-текст команди праворуч від бейджа
                    var lblCmdDesc = new Label
                    {
                        Text      = cmd.Value,
                        Location  = new Point(badge.Left + 80, cy + 1),
                        Size      = new Size(cardWidth - 100, 20),
                        ForeColor = descColor,
                        Font      = new Font("Segoe UI", 7.5f),
                        BackColor = Color.Transparent,
                    };
                    card.Controls.Add(lblCmdDesc);
                    cy += 24;
                }

                pnlPlugins.Controls.Add(card);
                y += cardH + 6;
                idx++;
            }

            pnlPlugins.Height = y + 8;
        }

        private void LoadMicrophones()
        {
            cmbMicrophone.Items.Clear();
            cmbMicrophone.Items.Add("(За замовчуванням системи)");
            try
            {
                var enumerator = new MMDeviceEnumerator();
                var devices = enumerator.EnumerateAudioEndPoints(DataFlow.Capture, DeviceState.Active);
                foreach (var device in devices)
                    cmbMicrophone.Items.Add(device.FriendlyName);
            }
            catch { /* NAudio недоступний */ }
            cmbMicrophone.SelectedIndex = 0;
        }

        private void LoadMicVolume()
        {
            try
            {
                string? selectedMic = cmbMicrophone.SelectedIndex > 0 ? cmbMicrophone.SelectedItem?.ToString() : null;
                var enumerator = new MMDeviceEnumerator();
                MMDevice? device = null;

                if (!string.IsNullOrEmpty(selectedMic))
                {
                    var devices = enumerator.EnumerateAudioEndPoints(DataFlow.Capture, DeviceState.Active);
                    device = devices.FirstOrDefault(d => d.FriendlyName == selectedMic);
                }
                device ??= enumerator.GetDefaultAudioEndpoint(DataFlow.Capture, Role.Communications);

                int vol = (int)Math.Round(device.AudioEndpointVolume.MasterVolumeLevelScalar * 100);
                trackMicVolume.Value = Math.Clamp(vol, 0, 100);
                lblMicVolumeValue.Text = vol + "%";
            }
            catch { }
        }

        private void SetMicVolume(int percent)
        {
            try
            {
                string? selectedMic = cmbMicrophone.SelectedIndex > 0 ? cmbMicrophone.SelectedItem?.ToString() : null;
                var enumerator = new MMDeviceEnumerator();
                MMDevice? device = null;

                if (!string.IsNullOrEmpty(selectedMic))
                {
                    var devices = enumerator.EnumerateAudioEndPoints(DataFlow.Capture, DeviceState.Active);
                    device = devices.FirstOrDefault(d => d.FriendlyName == selectedMic);
                }
                device ??= enumerator.GetDefaultAudioEndpoint(DataFlow.Capture, Role.Communications);

                device.AudioEndpointVolume.MasterVolumeLevelScalar = percent / 100f;
            }
            catch { }
        }

        // ─── Завантаження ─────────────────────────────────────────

        private void LoadConfig()
        {
            if (!File.Exists(_configPath))
            {
                MessageBox.Show($"config.json не знайдено:\n{_configPath}", "Помилка",
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            var json = File.ReadAllText(_configPath);
            _config = JsonConvert.DeserializeObject<ConfigModel>(json) ?? new ConfigModel();

            // Токени
            txtPicovoiceKey.Text = _config.PicovoiceAccessKey;
            txtOpenAiKey.Text    = _config.OpenaiApiKey;

            // Wake Word
            rbCustomWakeWord.Checked   = _config.WakeWordMode == "custom";
            rbStandardWakeWord.Checked = _config.WakeWordMode != "custom";

            int wakeIdx = cmbWakeWordStandard.Items.IndexOf(_config.WakeWordStandard);
            cmbWakeWordStandard.SelectedIndex = wakeIdx >= 0 ? wakeIdx : 0;

            txtCustomWakeWordPath.Text = _config.CustomWakeWordPath;
            trackSensitivity.Value     = Math.Clamp((int)(_config.Sensitivity * 100), 0, 100);
            lblSensitivityValue.Text   = _config.Sensitivity.ToString("F2");

            // TTS
            chkTtsEnabled.Checked = _config.TtsEnabled;
            txtTtsRate.Text       = _config.TtsRate;

            // Голос — шукаємо за ключем
            cmbTtsVoice.SelectedIndex = 0;
            for (int i = 0; i < cmbTtsVoice.Items.Count; i++)
            {
                if (cmbTtsVoice.Items[i] is VoiceComboItem item && item.Key == _config.TtsVoice)
                {
                    cmbTtsVoice.SelectedIndex = i;
                    break;
                }
            }

            // Мови — виставляємо чекбокси
            // Підтримуємо старе поле "language" і нове "languages"
            var activeLangs = _config.Languages;
            if (activeLangs == null || activeLangs.Count == 0)
                activeLangs = new List<string> { "uk-UA", "ru-RU", "en-US" };

            foreach (var kv in _langCheckboxes)
                kv.Value.Checked = activeLangs.Contains(kv.Key);

            // Таймаути
            nudCommandTimeout.Value    = Math.Clamp(_config.CommandSessionTimeout,  (int)nudCommandTimeout.Minimum,  (int)nudCommandTimeout.Maximum);
            nudContinuousListen.Value  = Math.Clamp(_config.ContinuousListenSeconds,(int)nudContinuousListen.Minimum,(int)nudContinuousListen.Maximum);
            nudSilenceDetect.Value     = Math.Clamp((decimal)_config.SilenceDetectSeconds, nudSilenceDetect.Minimum, nudSilenceDetect.Maximum);
            nudSilenceTimeout.Value    = Math.Clamp((decimal)_config.SilenceTimeout,       nudSilenceTimeout.Minimum, nudSilenceTimeout.Maximum);

            // Мікрофон
            cmbMicrophone.SelectedIndex = 0;
            if (!string.IsNullOrEmpty(_config.MicrophoneDevice))
            {
                int idx = cmbMicrophone.Items.IndexOf(_config.MicrophoneDevice);
                if (idx >= 0) cmbMicrophone.SelectedIndex = idx;
            }

            // Гучність мікрофону — спочатку беремо з системи, потім з config (якщо задано)
            LoadMicVolume();
            if (_config.MicrophoneVolume >= 0)
            {
                trackMicVolume.Value = Math.Clamp(_config.MicrophoneVolume, 0, 100);
                lblMicVolumeValue.Text = _config.MicrophoneVolume + "%";
            }

            // Gemini STT / моделі
            chkUseGeminiSTT.Checked = _config.UseGeminiSTT;
            txtRoutingModel.Text    = _config.RoutingModel;
            txtPluginModel.Text     = _config.PluginModel;

            // Плагіни — виставляємо чекбокси (disabled = відмічений = вимкнений → знятий)
            var disabled = _config.DisabledPlugins ?? new List<string>();
            foreach (var kv in _pluginCheckboxes)
                kv.Value.Checked = !disabled.Contains(kv.Key);

            UpdateWakeWordMode();
        }

        // ─── Збереження ───────────────────────────────────────────

        private void SaveConfig()
        {
            _config.PicovoiceAccessKey = txtPicovoiceKey.Text.Trim();
            _config.OpenaiApiKey       = txtOpenAiKey.Text.Trim();

            _config.WakeWordMode      = rbCustomWakeWord.Checked ? "custom" : "standard";
            _config.WakeWordStandard  = cmbWakeWordStandard.SelectedItem?.ToString() ?? "alexa";
            _config.CustomWakeWordPath = txtCustomWakeWordPath.Text.Trim();
            _config.Sensitivity       = trackSensitivity.Value / 100.0;

            // Голос — зберігаємо внутрішній ключ
            if (cmbTtsVoice.SelectedItem is VoiceComboItem voiceItem)
                _config.TtsVoice = voiceItem.Key;

            _config.TtsRate    = txtTtsRate.Text.Trim();
            _config.TtsEnabled = chkTtsEnabled.Checked;

            // Мови — збираємо відмічені чекбокси
            _config.Languages = _langCheckboxes
                .Where(kv => kv.Value.Checked)
                .Select(kv => kv.Key)
                .ToList();

            if (_config.Languages.Count == 0)
            {
                MessageBox.Show("Потрібно обрати хоча б одну мову розпізнавання.", "Увага",
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            _config.CommandSessionTimeout  = (int)nudCommandTimeout.Value;
            _config.ContinuousListenSeconds = (int)nudContinuousListen.Value;
            _config.SilenceDetectSeconds   = (double)nudSilenceDetect.Value;
            _config.SilenceTimeout         = (double)nudSilenceTimeout.Value;

            _config.MicrophoneDevice = cmbMicrophone.SelectedIndex <= 0
                ? ""
                : cmbMicrophone.SelectedItem!.ToString()!;

            _config.MicrophoneVolume = trackMicVolume.Value;
            SetMicVolume(trackMicVolume.Value);

            // Gemini STT / моделі
            _config.UseGeminiSTT  = chkUseGeminiSTT.Checked;
            _config.RoutingModel  = txtRoutingModel.Text.Trim();
            _config.PluginModel   = txtPluginModel.Text.Trim();

            // Плагіни — зберігаємо список вимкнених
            _config.DisabledPlugins = _pluginCheckboxes
                .Where(kv => !kv.Value.Checked)
                .Select(kv => kv.Key)
                .ToList();

            try
            {
                var json = JsonConvert.SerializeObject(_config, Formatting.Indented);
                File.WriteAllText(_configPath, json);
                MessageBox.Show("Налаштування збережено успішно!", "Готово",
                    MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Помилка збереження:\n{ex.Message}", "Помилка",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        // ─── Допоміжні ────────────────────────────────────────────

        private void UpdateWakeWordMode()
        {
            bool isCustom = rbCustomWakeWord.Checked;
            cmbWakeWordStandard.Enabled     = !isCustom;
            lblWakeWordStandardLabel.Enabled = !isCustom;
            txtCustomWakeWordPath.Enabled   = isCustom;
            btnBrowsePpn.Enabled            = isCustom;
            lblCustomWakeWordPath.Enabled   = isCustom;
            lblCustomWakeWordHint.Enabled   = isCustom;
        }

        // ─── Автозапуск ───────────────────────────────────────────

        /// <summary>Знаходить Alexa.exe поряд з поточним exe або в dist/Alexa/.</summary>
        private static string? FindAlexaExe()
        {
            // Варіант 1: поряд з AlexaSettings.exe (в dist/Alexa/)
            string dir = AppDomain.CurrentDomain.BaseDirectory;
            string candidate = Path.Combine(dir, "Alexa.exe");
            if (File.Exists(candidate)) return candidate;

            // Варіант 2: шукаємо вгору від AlexaSettings.exe
            string? parent = Path.GetDirectoryName(dir);
            if (parent != null)
            {
                candidate = Path.Combine(parent, "Alexa", "Alexa.exe");
                if (File.Exists(candidate)) return candidate;
            }
            return null;
        }

        private void LoadAutostartState()
        {
            string? alexaExe = FindAlexaExe();
            if (alexaExe != null)
                lblAutostartPath.Text = "Шлях: " + alexaExe;
            else
                lblAutostartPath.Text = "Alexa.exe не знайдено (запустіть після білду)";

            try
            {
                using var key = Registry.CurrentUser.OpenSubKey(AutostartRegKey, false);
                string? val = key?.GetValue(AutostartAppName) as string;
                // Знімаємо обробник щоб не тригерити зміни при завантаженні
                chkAutostart.CheckedChanged -= chkAutostart_CheckedChanged;
                chkAutostart.Checked = !string.IsNullOrEmpty(val);
                chkAutostart.CheckedChanged += chkAutostart_CheckedChanged;
            }
            catch { }
        }

        private void SetAutostart(bool enable)
        {
            try
            {
                using var key = Registry.CurrentUser.OpenSubKey(AutostartRegKey, true);
                if (key == null) return;

                if (enable)
                {
                    string? alexaExe = FindAlexaExe();
                    if (alexaExe == null)
                    {
                        // Пропонуємо вибрати Alexa.exe вручну
                        using var ofd = new OpenFileDialog
                        {
                            Title = "Вкажіть розташування Alexa.exe",
                            Filter = "Alexa.exe|Alexa.exe|Всі файли|*.exe",
                            FileName = "Alexa.exe"
                        };
                        if (ofd.ShowDialog() != DialogResult.OK)
                        {
                            chkAutostart.CheckedChanged -= chkAutostart_CheckedChanged;
                            chkAutostart.Checked = false;
                            chkAutostart.CheckedChanged += chkAutostart_CheckedChanged;
                            return;
                        }
                        alexaExe = ofd.FileName;
                    }
                    key.SetValue(AutostartAppName, $"\"{alexaExe}\"");
                    lblAutostartPath.Text = "Шлях: " + alexaExe;
                    MessageBox.Show("Alexa додана до автозапуску Windows.", "Готово",
                        MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                else
                {
                    key.DeleteValue(AutostartAppName, throwOnMissingValue: false);
                    MessageBox.Show("Alexa видалена з автозапуску Windows.", "Готово",
                        MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Помилка зміни автозапуску:\n{ex.Message}", "Помилка",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        // ─── Events ───────────────────────────────────────────────

        private void btnSave_Click(object sender, EventArgs e) => SaveConfig();

        private void btnBrowsePpn_Click(object sender, EventArgs e)
        {
            using var dlg = new OpenFileDialog
            {
                Filter = "Picovoice Wake Word (*.ppn)|*.ppn",
                Title  = "Виберіть .ppn файл"
            };
            if (!string.IsNullOrEmpty(txtCustomWakeWordPath.Text))
            {
                var dir = Path.GetDirectoryName(txtCustomWakeWordPath.Text);
                if (Directory.Exists(dir)) dlg.InitialDirectory = dir;
            }
            if (dlg.ShowDialog() == DialogResult.OK)
                txtCustomWakeWordPath.Text = dlg.FileName;
        }

        private void rbCustomWakeWord_CheckedChanged(object sender, EventArgs e)   => UpdateWakeWordMode();
        private void rbStandardWakeWord_CheckedChanged(object sender, EventArgs e) => UpdateWakeWordMode();

        private void trackSensitivity_Scroll(object sender, EventArgs e)
            => lblSensitivityValue.Text = (trackSensitivity.Value / 100.0).ToString("F2");

        private void chkAutostart_CheckedChanged(object? sender, EventArgs e)
            => SetAutostart(chkAutostart.Checked);

        private void btnReload_Click(object sender, EventArgs e)
        {
            LoadMicrophones();
            LoadConfig();
            MessageBox.Show("Налаштування перезавантажено.", "Оновлено",
                MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        private void trackMicVolume_Scroll(object sender, EventArgs e)
        {
            lblMicVolumeValue.Text = trackMicVolume.Value + "%";
            SetMicVolume(trackMicVolume.Value);
        }

        private void btnMicTest_Click(object sender, EventArgs e)
        {
            if (_micTestRunning)
            {
                StopMicTest();
                btnMicTest.Text = "▶ Почати тест";
            }
            else
            {
                StartMicTest();
                btnMicTest.Text = "⏹ Зупинити";
            }
        }

        private void StartMicTest()
        {
            try
            {
                // Знаходимо індекс пристрою для WaveIn
                int deviceIndex = 0;
                string? selectedMic = cmbMicrophone.SelectedIndex > 0 ? cmbMicrophone.SelectedItem?.ToString() : null;
                if (!string.IsNullOrEmpty(selectedMic))
                {
                    for (int i = 0; i < WaveIn.DeviceCount; i++)
                    {
                        var caps = WaveIn.GetCapabilities(i);
                        if (caps.ProductName.Contains(selectedMic[..Math.Min(31, selectedMic.Length)], StringComparison.OrdinalIgnoreCase))
                        {
                            deviceIndex = i;
                            break;
                        }
                    }
                }

                _micTestCapture = new WaveInEvent
                {
                    DeviceNumber = deviceIndex,
                    WaveFormat = new WaveFormat(16000, 16, 1),
                    BufferMilliseconds = 50
                };

                _micTestCapture.DataAvailable += (s, args) =>
                {
                    // Обчислюємо RMS рівень
                    float sum = 0;
                    int count = args.BytesRecorded / 2;
                    for (int i = 0; i < args.BytesRecorded - 1; i += 2)
                    {
                        short sample = BitConverter.ToInt16(args.Buffer, i);
                        float normalized = sample / 32768f;
                        sum += normalized * normalized;
                    }
                    float rms = count > 0 ? (float)Math.Sqrt(sum / count) : 0f;
                    _currentMicLevel = Math.Min(rms * 5f, 1f); // посилення x5 для видимості
                };

                _micTestCapture.StartRecording();

                // Таймер для оновлення ProgressBar
                _micTestTimer = new System.Windows.Forms.Timer { Interval = 50 };
                _micTestTimer.Tick += (s, e) =>
                {
                    int level = (int)(_currentMicLevel * 100);
                    pbMicLevel.Value = Math.Clamp(level, 0, 100);

                    // Змінюємо колір залежно від рівня
                    if (level > 80) pbMicLevel.ForeColor = Color.FromArgb(200, 50, 50);
                    else if (level > 50) pbMicLevel.ForeColor = Color.FromArgb(220, 160, 0);
                    else pbMicLevel.ForeColor = Color.FromArgb(37, 150, 90);
                };
                _micTestTimer.Start();
                _micTestRunning = true;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Помилка запуску тесту мікрофону:\n{ex.Message}", "Помилка",
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }

        private void StopMicTest()
        {
            _micTestRunning = false;
            _micTestTimer?.Stop();
            _micTestTimer?.Dispose();
            _micTestTimer = null;
            _micTestCapture?.StopRecording();
            _micTestCapture?.Dispose();
            _micTestCapture = null;
            pbMicLevel.Value = 0;
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            StopMicTest();
            base.OnFormClosing(e);
        }

        private void btnEye_Click(object sender, EventArgs e)
        {
            if (sender is Button btn && btn.Tag is TextBox txt)
                txt.UseSystemPasswordChar = !txt.UseSystemPasswordChar;
        }

        private void btnCopy_Click(object sender, EventArgs e)
        {
            if (sender is Button btn && btn.Tag is TextBox txt && !string.IsNullOrEmpty(txt.Text))
            {
                Clipboard.SetText(txt.Text);
                var originalText = btn.Text;
                btn.Text = "✓";
                var t = new System.Windows.Forms.Timer { Interval = 1200 };
                t.Tick += (_, __) => { btn.Text = originalText; t.Stop(); t.Dispose(); };
                t.Start();
            }
        }
    }

    /// <summary>Елемент для ComboBox голосів — показує людську назву, зберігає ключ.</summary>
    public class VoiceComboItem
    {
        public string Key         { get; }
        public string DisplayName { get; }
        public VoiceComboItem(string key, string displayName) { Key = key; DisplayName = displayName; }
        public override string ToString() => DisplayName;
    }
}
