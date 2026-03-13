using Microsoft.Win32;
using NAudio.CoreAudioApi;
using Newtonsoft.Json;

namespace AlexaSettings
{
    public partial class MainForm : Form
    {
        private string _configPath;
        private ConfigModel _config = new();

        // Чекбокси мов — будуємо динамічно
        private readonly Dictionary<string, CheckBox> _langCheckboxes = new();

        // Ключ реєстру для автозапуску
        private const string AutostartRegKey = @"SOFTWARE\Microsoft\Windows\CurrentVersion\Run";
        private const string AutostartAppName = "AlexaAssistant";

        public MainForm()
        {
            InitializeComponent();
            _configPath = FindConfigPath();
            lblConfigPath.Text = "config.json: " + _configPath;

            InitVoiceCombo();
            BuildLanguageCheckboxes();
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
