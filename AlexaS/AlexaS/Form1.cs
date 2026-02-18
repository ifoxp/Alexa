using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Linq;
using System.Media;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Windows.Forms;
using System.Runtime.InteropServices;

namespace AlexaS
{
    public partial class Form1 : Form
    {
        // Windows API для відтворення звуку
        [DllImport("winmm.dll")]
        private static extern bool PlaySound(string pszSound, IntPtr hmod, uint fdwSound);

        private const uint SND_FILENAME = 0x00020000;
        private const uint SND_ASYNC = 0x00000001;

        // Клас для конфігурації
        public class VoiceConfig
        {
            public string PicovoiceAccessKey { get; set; } = string.Empty;
            public string OpenaiApiKey { get; set; } = string.Empty;
            public string WakeWordMode { get; set; } = "standard";
            public string WakeWordStandard { get; set; } = "alexa";
            public string CustomWakeWordPath { get; set; } = string.Empty;
            public double Sensitivity { get; set; } = 0.5;
            public int CommandSessionTimeout { get; set; } = 15;
            public int ContinuousListenSeconds { get; set; } = 7;
            public double SilenceDetectSeconds { get; set; } = 1.5;
            public double SilenceTimeout { get; set; } = 5.0;
            public bool TtsEnabled { get; set; } = true;
            public string TtsVoice { get; set; } = "jarvis"; // jarvis (чоловічий) або polina (жіночий)
            public int TtsSpeed { get; set; } = 30; // швидкість від -50 до +100
        }

        private VoiceConfig config;
        private const string ConfigPath = "config.json";

        public Form1()
        {
            InitializeComponent();
            LoadConfiguration();
            ApplyModernTheme();
            SetupEventHandlers();
            UpdateUI();
        }

        private void ApplyModernTheme()
        {
            // Сучасний темний дизайн
            this.BackColor = Color.FromArgb(25, 25, 25);
            this.ForeColor = Color.White;
            this.Font = new Font("Segoe UI", 10F, FontStyle.Regular);

            // Видаляємо границі вікна для сучасного вигляду
            this.FormBorderStyle = FormBorderStyle.FixedSingle;
            this.MaximizeBox = false;
            this.StartPosition = FormStartPosition.CenterScreen;
        }

        private void SetupEventHandlers()
        {
            // Обробники подій
            this.FormClosing += Form1_FormClosing;
        }

        private void LoadConfiguration()
        {
            try
            {
                if (File.Exists(ConfigPath))
                {
                    string json = File.ReadAllText(ConfigPath);

                    // Парсимо JSON вручну, щоб конвертувати назви полів
                    using (JsonDocument doc = JsonDocument.Parse(json))
                    {
                        config = new VoiceConfig();
                        var root = doc.RootElement;

                        if (root.TryGetProperty("picovoiceAccessKey", out var picoKey))
                            config.PicovoiceAccessKey = picoKey.GetString() ?? "";

                        if (root.TryGetProperty("openaiApiKey", out var openaiKey))
                            config.OpenaiApiKey = openaiKey.GetString() ?? "";

                        if (root.TryGetProperty("wakeWordMode", out var wakeMode))
                            config.WakeWordMode = wakeMode.GetString() ?? "standard";

                        if (root.TryGetProperty("wakeWordStandard", out var wakeStd))
                            config.WakeWordStandard = wakeStd.GetString() ?? "alexa";

                        if (root.TryGetProperty("customWakeWordPath", out var wakePath))
                            config.CustomWakeWordPath = wakePath.GetString() ?? "";

                        if (root.TryGetProperty("sensitivity", out var sens))
                            config.Sensitivity = sens.GetDouble();

                        if (root.TryGetProperty("commandSessionTimeout", out var cmdTimeout))
                            config.CommandSessionTimeout = cmdTimeout.GetInt32();

                        if (root.TryGetProperty("continuousListenSeconds", out var contListen))
                            config.ContinuousListenSeconds = contListen.GetInt32();

                        if (root.TryGetProperty("silenceDetectSeconds", out var silDetect))
                            config.SilenceDetectSeconds = silDetect.GetDouble();

                        if (root.TryGetProperty("silenceTimeout", out var silTimeout))
                            config.SilenceTimeout = silTimeout.GetDouble();

                        if (root.TryGetProperty("ttsEnabled", out var ttsEn))
                            config.TtsEnabled = ttsEn.GetBoolean();

                        if (root.TryGetProperty("ttsVoice", out var ttsVoice))
                            config.TtsVoice = ttsVoice.GetString() ?? "jarvis";

                        // Завантажуємо швидкість TTS з поля ttsRate (конвертуємо з "+40%" в число)
                        if (root.TryGetProperty("ttsRate", out var ttsRate))
                        {
                            string rateStr = ttsRate.GetString() ?? "+40%";
                            int speed;
                            if (rateStr.StartsWith("+"))
                            {
                                if (int.TryParse(rateStr.Substring(1, rateStr.Length - 2), out speed))
                                    config.TtsSpeed = speed;
                            }
                            else if (rateStr.StartsWith("-"))
                            {
                                if (int.TryParse(rateStr.Substring(0, rateStr.Length - 1), out speed))
                                    config.TtsSpeed = speed;
                            }
                        }
                    }
                }
                else
                {
                    config = new VoiceConfig();
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Помилка завантаження конфігурації: {ex.Message}",
                    "Помилка", MessageBoxButtons.OK, MessageBoxIcon.Error);
                config = new VoiceConfig();
            }
        }

        private void SaveConfiguration()
        {
            try
            {
                // Створюємо JSON об'єкт з правильними назвами полів для Python
                var jsonConfig = new
                {
                    picovoiceAccessKey = config.PicovoiceAccessKey,
                    openaiApiKey = config.OpenaiApiKey,
                    wakeWordMode = config.WakeWordMode,
                    wakeWordStandard = config.WakeWordStandard,
                    customWakeWordPath = config.CustomWakeWordPath,
                    sensitivity = config.Sensitivity,
                    language = "uk-UA",
                    commandSessionTimeout = config.CommandSessionTimeout,
                    continuousListenSeconds = config.ContinuousListenSeconds,
                    silenceDetectSeconds = config.SilenceDetectSeconds,
                    silenceTimeout = config.SilenceTimeout,
                    aiAssistantEnabled = true,
                    ttsEnabled = config.TtsEnabled,
                    ttsEngine = "edge",
                    ttsVoice = config.TtsVoice,
                    ttsSpeed = 1,
                    ttsRate = config.TtsSpeed >= 0 ? $"+{config.TtsSpeed}%" : $"{config.TtsSpeed}%",
                    ttsLanguage = "uk",
                    elevenLabsApiKey = ""
                };

                var options = new JsonSerializerOptions
                {
                    WriteIndented = true,
                    Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping
                };

                string json = JsonSerializer.Serialize(jsonConfig, options);
                File.WriteAllText(ConfigPath, json);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Помилка збереження конфігурації: {ex.Message}",
                    "Помилка", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void UpdateUI()
        {
            // Оновлюємо всі контроли значеннями з конфігурації
            txtPicovoiceKey.Text = config.PicovoiceAccessKey;
            txtOpenAIKey.Text = config.OpenaiApiKey;

            if (config.WakeWordMode == "standard")
                rbStandardWakeWord.Checked = true;
            else
                rbCustomWakeWord.Checked = true;

            cmbWakeWordStandard.SelectedItem = config.WakeWordStandard;
            txtCustomWakeWordPath.Text = config.CustomWakeWordPath;

            trackSensitivity.Value = (int)(config.Sensitivity * 100);
            numCommandTimeout.Value = config.CommandSessionTimeout;
            numListenSeconds.Value = config.ContinuousListenSeconds;
            numSilenceDetect.Value = (decimal)config.SilenceDetectSeconds;
            numSilenceTimeout.Value = (decimal)config.SilenceTimeout;

            chkTtsEnabled.Checked = config.TtsEnabled;

            if (config.TtsVoice == "jarvis")
                rbMaleVoice.Checked = true;
            else
                rbFemaleVoice.Checked = true;

            // Оновлюємо швидкість TTS
            trackVoiceSpeed.Value = config.TtsSpeed;
            lblVoiceSpeedValue.Text = config.TtsSpeed >= 0 ? $"+{config.TtsSpeed}%" : $"{config.TtsSpeed}%";

            UpdateWakeWordControls();
            UpdateVoiceSpeedLabel();
        }

        private void UpdateWakeWordControls()
        {
            bool isStandard = rbStandardWakeWord.Checked;
            cmbWakeWordStandard.Enabled = isStandard;
            txtCustomWakeWordPath.Enabled = !isStandard;
            btnBrowseWakeWord.Enabled = !isStandard;
        }

        private void UpdateVoiceSpeedLabel()
        {
            lblVoiceSpeedValue.Text = config.TtsSpeed >= 0 ? $"+{config.TtsSpeed}%" : $"{config.TtsSpeed}%";
        }

        private void Form1_FormClosing(object sender, FormClosingEventArgs e)
        {
            SaveConfiguration();
        }

        // Обробники подій для контролів
        private void rbStandardWakeWord_CheckedChanged(object sender, EventArgs e)
        {
            config.WakeWordMode = rbStandardWakeWord.Checked ? "standard" : "custom";
            UpdateWakeWordControls();
        }

        private void rbCustomWakeWord_CheckedChanged(object sender, EventArgs e)
        {
            config.WakeWordMode = rbCustomWakeWord.Checked ? "custom" : "standard";
            UpdateWakeWordControls();
        }

        private void cmbWakeWordStandard_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (cmbWakeWordStandard.SelectedItem != null)
                config.WakeWordStandard = cmbWakeWordStandard.SelectedItem.ToString();
        }

        private void btnBrowseWakeWord_Click(object sender, EventArgs e)
        {
            using (OpenFileDialog ofd = new OpenFileDialog())
            {
                ofd.Filter = "Picovoice Wake Word (*.ppn)|*.ppn|Всі файли (*.*)|*.*";
                ofd.Title = "Виберіть файл wake word";

                if (ofd.ShowDialog() == DialogResult.OK)
                {
                    txtCustomWakeWordPath.Text = ofd.FileName;
                    config.CustomWakeWordPath = ofd.FileName;
                }
            }
        }

        private void txtPicovoiceKey_TextChanged(object sender, EventArgs e)
        {
            config.PicovoiceAccessKey = txtPicovoiceKey.Text;
        }

        private void txtOpenAIKey_TextChanged(object sender, EventArgs e)
        {
            config.OpenaiApiKey = txtOpenAIKey.Text;
        }

        private void trackSensitivity_Scroll(object sender, EventArgs e)
        {
            config.Sensitivity = trackSensitivity.Value / 100.0;
            lblSensitivityValue.Text = $"{config.Sensitivity:F2}";
        }

        private void numCommandTimeout_ValueChanged(object sender, EventArgs e)
        {
            config.CommandSessionTimeout = (int)numCommandTimeout.Value;
        }

        private void numListenSeconds_ValueChanged(object sender, EventArgs e)
        {
            config.ContinuousListenSeconds = (int)numListenSeconds.Value;
        }

        private void numSilenceDetect_ValueChanged(object sender, EventArgs e)
        {
            config.SilenceDetectSeconds = (double)numSilenceDetect.Value;
        }

        private void numSilenceTimeout_ValueChanged(object sender, EventArgs e)
        {
            config.SilenceTimeout = (double)numSilenceTimeout.Value;
        }

        private void chkTtsEnabled_CheckedChanged(object sender, EventArgs e)
        {
            config.TtsEnabled = chkTtsEnabled.Checked;
        }

        private void rbMaleVoice_CheckedChanged(object sender, EventArgs e)
        {
            if (rbMaleVoice.Checked)
                config.TtsVoice = "jarvis";
        }

        private void rbFemaleVoice_CheckedChanged(object sender, EventArgs e)
        {
            if (rbFemaleVoice.Checked)
                config.TtsVoice = "polina";
        }

        private void btnSaveAndClose_Click(object sender, EventArgs e)
        {
            SaveConfiguration();
            this.Close();
        }

        private void btnLaunchAlexa_Click(object sender, EventArgs e)
        {
            try
            {
                SaveConfiguration();

                // Шукаємо Alexa.exe в тій же папці що і налаштування
                string alexaExePath = Path.Combine(Application.StartupPath, "Alexa.exe");
                if (File.Exists(alexaExePath))
                {
                    ProcessStartInfo startInfo = new ProcessStartInfo
                    {
                        FileName = alexaExePath,
                        WorkingDirectory = Application.StartupPath,
                        UseShellExecute = false,
                        CreateNoWindow = true,  // Приховуємо консоль
                        WindowStyle = ProcessWindowStyle.Hidden
                    };
                    Process.Start(startInfo);
                    MessageBox.Show("Асистента запущено!", "Інформація",
                        MessageBoxButtons.OK, MessageBoxIcon.Information);
                }
                else
                {
                    MessageBox.Show("Не знайдено файл Alexa.exe в тій же папці", "Помилка",
                        MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Помилка запуску: {ex.Message}", "Помилка",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        // Нові обробники подій
        private void trackVoiceSpeed_Scroll(object sender, EventArgs e)
        {
            config.TtsSpeed = trackVoiceSpeed.Value;
            UpdateVoiceSpeedLabel();
        }

        private void btnTestVoice_Click(object sender, EventArgs e)
        {
            try
            {
                // Створюємо тестове TTS повідомлення
                string testMessage = "Привіт! Це тест голосового асистента. Швидкість мовлення налаштовано правильно.";
                string voiceType = config.TtsVoice;
                string rate = config.TtsSpeed >= 0 ? $"+{config.TtsSpeed}%" : $"{config.TtsSpeed}%";

                // Створюємо тимчасовий файл для тесту
                string tempWav = Path.Combine(Path.GetTempPath(), "alexa_test.wav");

                // Запускаємо Edge TTS для генерації тестового аудіо
                ProcessStartInfo startInfo = new ProcessStartInfo
                {
                    FileName = "python",
                    Arguments = $"-m edge_tts --voice uk-UA-{(voiceType == "jarvis" ? "Ostap" : "Polina")}Neural --rate {rate} --text \"{testMessage}\" --write-media \"{tempWav}\"",
                    UseShellExecute = false,
                    CreateNoWindow = true,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true
                };

                using (Process process = Process.Start(startInfo))
                {
                    process.WaitForExit();

                    if (process.ExitCode == 0 && File.Exists(tempWav))
                    {
                        // Відтворюємо згенерований файл через Windows API (без відкриття медіаплеєра)
                        PlaySound(tempWav, IntPtr.Zero, SND_FILENAME | SND_ASYNC);

                        // Видаляємо тимчасовий файл через 10 секунд
                        var timer = new System.Windows.Forms.Timer();
                        timer.Interval = 10000; // 10 секунд
                        timer.Tick += (s, args) =>
                        {
                            timer.Stop();
                            if (File.Exists(tempWav))
                            {
                                try { File.Delete(tempWav); } catch { }
                            }
                        };
                        timer.Start();
                    }
                    else
                    {
                        MessageBox.Show("Не вдалося створити тестове аудіо. Переконайтеся що edge-tts встановлено.",
                            "Помилка", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Помилка тестування голосу: {ex.Message}", "Помилка",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void btnSaveAndRestart_Click(object sender, EventArgs e)
        {
            try
            {
                SaveConfiguration();

                // Знаходимо процес Alexa якщо він запущений
                try
                {
                    var processes = Process.GetProcessesByName("Alexa");
                    foreach (var proc in processes)
                    {
                        proc.Kill();
                        proc.WaitForExit(3000); // Чекаємо до 3 секунд
                    }
                }
                catch { } // Ігноруємо помилки завершення процесів

                // Запускаємо знову
                string alexaExePath = Path.Combine(Application.StartupPath, "Alexa.exe");
                if (File.Exists(alexaExePath))
                {
                    ProcessStartInfo startInfo = new ProcessStartInfo
                    {
                        FileName = alexaExePath,
                        WorkingDirectory = Application.StartupPath,
                        UseShellExecute = false,
                        CreateNoWindow = true,  // Приховуємо консоль
                        WindowStyle = ProcessWindowStyle.Hidden
                    };
                    Process.Start(startInfo);
                    MessageBox.Show("Конфігурацію збережено та асистента перезапущено!", "Успіх",
                        MessageBoxButtons.OK, MessageBoxIcon.Information);
                    this.Close();
                }
                else
                {
                    MessageBox.Show("Конфігурацію збережено, але не знайдено файл Alexa.exe для запуску", "Попередження",
                        MessageBoxButtons.OK, MessageBoxIcon.Warning);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Помилка перезапуску: {ex.Message}", "Помилка",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }
    }
}