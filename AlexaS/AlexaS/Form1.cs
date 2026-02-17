using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Linq;
using System.Text.Encodings.Web;
using System.Text.Json;
using System.Windows.Forms;
using System.Runtime.InteropServices;

namespace AlexaS
{
    public partial class Form1 : Form
    {
        // Windows API для приховування scrollbar
        [DllImport("user32.dll")]
        private static extern int ShowScrollBar(IntPtr hWnd, int wBar, int bShow);

        private const int SB_VERT = 1;
        private const int SB_HORZ = 0;

        // Клас для представлення вашої конфігурації
        public class JarvisConfig
        {
            public string PicovoiceAccessKey { get; set; } = string.Empty;
            public string WakeWordMode { get; set; } = "standard";
            public string WakeWordStandard { get; set; } = "jarvis";
            public string CustomWakeWordPath { get; set; } = string.Empty;
            public double Sensitivity { get; set; } = 0.5;
            // Видалено Language - тепер багатомовний режим автоматично
            public int CommandSessionTimeout { get; set; } = 15;
            public int ContinuousListenSeconds { get; set; } = 7;
            public double SilenceDetectSeconds { get; set; } = 1.5;
        }

        // Клас для представлення окремої дії в команді
        public class CommandAction
        {
            public string Type { get; set; } = string.Empty;
            public string Target { get; set; } = string.Empty;
        }

        // Клас для представлення команди
        public class VoiceCommand
        {
            public string Name { get; set; } = string.Empty;
            public List<string> Phrases { get; set; } = new List<string>();

            // Для стандартного формату (одна дія)
            public string Type { get; set; } = string.Empty;
            public string Target { get; set; } = string.Empty;

            // Для розширеного формату (множинні дії)
            public List<CommandAction> Actions { get; set; } = new List<CommandAction>();

            public bool RequiresArgument { get; set; } = false;
            public string FileName { get; set; } = string.Empty; // для зберігання імені файлу

            // Властивість для визначення чи це комбінована команда
            public bool IsCombinedCommand => Actions != null && Actions.Count > 0;

            // Властивість для отримання типу команди (для відображення в списку)
            public string DisplayType
            {
                get
                {
                    if (IsCombinedCommand)
                    {
                        return $"🔗 Комбінація ({Actions.Count} дій)";
                    }
                    return Type;
                }
            }
        }

        private string _jarvisExePath;
        private string _configPath;
        private const string ConfigFileName = "config.json";

        // Змінні для режиму управління командами
        private bool _isCommandsMode = false;
        private List<VoiceCommand> _loadedCommands = new List<VoiceCommand>();
        private string _commandsPath;

        // Кешовані панелі команд для швидкого переключення
        private Panel _commandsLeftPanel = null;
        private Panel _commandsRightPanel = null;
        private ListView _commandsListView = null;
        private Panel _commandDetailsPanel = null;

        public Form1()
        {
            InitializeComponent();
            InitializeEventHandlers();
        }

        private void InitializeEventHandlers()
        {
            // Прив'язка подій до методів
            this.Load += Form1_Load;
            this.btnSelectJarvis.Click += BtnSelectJarvis_Click;

            // Picovoice
            this.btnPicovoiceHelp.Click += BtnPicovoiceHelp_Click;
            this.btnPicovoiceWebsite.Click += BtnPicovoiceWebsite_Click;

            // Wake Word
            this.radioStandard.CheckedChanged += RadioWakeWord_CheckedChanged;
            this.radioCustom.CheckedChanged += RadioWakeWord_CheckedChanged;
            this.btnBrowseCustomWakeWord.Click += BtnBrowseCustomWakeWord_Click;

            // Чутливість
            this.trackSensitivity.Scroll += TrackSensitivity_Scroll;

            // Кнопки дій
            this.btnSave.Click += BtnSave_Click;
            this.btnSaveAndRestart.Click += BtnSaveAndRestart_Click;
            this.btnManageCommands.Click += BtnManageCommands_Click;

            // ✨ ДОДАЄМО КАСТОМНИЙ СКРОЛ
            InitializeCustomScroll();
        }

        #region Paint Events (Градієнти та Бордери)

        /// <summary>
        /// Налаштовує скрол колесом миші без видимого scrollbar.
        /// </summary>
        private void InitializeCustomScroll()
        {
            // AutoScroll вже true з Designer - не змінюємо!

            // Приховуємо scrollbar після створення Handle
            panelMain.HandleCreated += (s, e) =>
            {
                ShowScrollBar(panelMain.Handle, SB_VERT, 0);
                ShowScrollBar(panelMain.Handle, SB_HORZ, 0);
            };

            // Якщо форма вже завантажена
            if (panelMain.IsHandleCreated)
            {
                ShowScrollBar(panelMain.Handle, SB_VERT, 0);
                ShowScrollBar(panelMain.Handle, SB_HORZ, 0);
            }
        }

        /// <summary>
        /// Малює градієнтний фон для панелі header.
        /// </summary>
        private void panelHeader_Paint(object sender, PaintEventArgs e)
        {
            Panel panel = sender as Panel;
            if (panel == null) return;

            using (LinearGradientBrush brush = new LinearGradientBrush(
                panel.ClientRectangle,
                Color.FromArgb(120, 160, 180),  // М'який синьо-сірий
                Color.FromArgb(90, 130, 160),   // Темніший синьо-сірий
                45F))
            {
                e.Graphics.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
                e.Graphics.FillRectangle(brush, panel.ClientRectangle);
            }
        }

        /// <summary>
        /// Малює тонкий бордер навколо карток.
        /// </summary>
        private void panelCard_Paint(object sender, PaintEventArgs e)
        {
            Panel panel = sender as Panel;
            if (panel == null) return;

            using (Pen pen = new Pen(Color.FromArgb(80, 90, 100), 1))
            {
                e.Graphics.DrawRectangle(pen, 0, 0, panel.Width - 1, panel.Height - 1);
            }
        }

        #endregion

        #region Button Hover Effects

        /// <summary>
        /// Hover ефект - світліший колір при наведенні.
        /// </summary>
        private void Button_MouseEnter(object sender, EventArgs e)
        {
            Button btn = sender as Button;
            if (btn == null) return;

            // Робимо колір світлішим
            btn.BackColor = ControlPaint.Light(btn.BackColor, 0.2f);
        }

        /// <summary>
        /// Повернення оригінального кольору при виході миші.
        /// </summary>
        private void Button_MouseLeave(object sender, EventArgs e)
        {
            Button btn = sender as Button;
            if (btn == null) return;

            // Відновлюємо оригінальні кольори
            if (btn == btnSelectJarvis || btn == btnPicovoiceHelp ||
                btn == btnBrowseCustomWakeWord || btn == btnSaveAndRestart)
            {
                btn.BackColor = Color.FromArgb(95, 135, 165);
            }
            else if (btn == btnPicovoiceWebsite || btn == btnManageCommands)
            {
                btn.BackColor = Color.FromArgb(110, 140, 170);
            }
            else if (btn == btnSave)
            {
                btn.BackColor = Color.FromArgb(70, 80, 90);
            }
        }

        #endregion

        #region TrackBar and RadioButton Events

        /// <summary>
        /// Оновлює лейбл при зміні значення чутливості.
        /// </summary>
        private void trackSensitivity_ValueChanged(object sender, EventArgs e)
        {
            UpdateSensitivityLabel();
        }

        /// <summary>
        /// Обробляє перемикання між custom та standard wake word.
        /// </summary>
        private void radioCustom_CheckedChanged(object sender, EventArgs e)
        {
            UpdateWakeWordControls();
        }

        #endregion

        #region 1. Ініціалізація та завантаження конфігурації

        private void Form1_Load(object sender, EventArgs e)
        {
            // 1. Спочатку шукаємо Alexa.exe в тій же папці
            string currentDir = Path.GetDirectoryName(Application.ExecutablePath);
            string alexaExePath = Path.Combine(currentDir, "Alexa.exe");

            if (File.Exists(alexaExePath))
            {
                // 2. Знайшли Alexa.exe в тій же папці - використовуємо його
                SetJarvisPaths(alexaExePath);
                LoadConfiguration();
            }
            else
            {
                // 3. Перевіряємо збережений шлях
                string savedPath = Properties.Settings.Default.JarvisPath;

                if (string.IsNullOrEmpty(savedPath) || !File.Exists(savedPath))
                {
                    // 4. Якщо шлях невалідний, змушуємо користувача вибрати його
                    MessageBox.Show(
                        "Alexa.exe не знайдено в поточній папці.\nБудь ласка, вкажіть шлях до виконуваного файлу Jarvis вручну.",
                        "Потрібно налаштувати",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Information);
                    SelectAndLoadJarvisPath();
                }
                else
                {
                    // 5. Якщо збережений шлях валідний, завантажуємо конфігурацію
                    SetJarvisPaths(savedPath);
                    LoadConfiguration();
                }
            }

            // Оновлюємо UI для Wake Word
            UpdateWakeWordControls();

            // Встановлюємо початкове значення чутливості
            UpdateSensitivityLabel();

            // Мову видалено - тепер багатомовний режим автоматично
        }

        /// <summary>
        /// Показує діалог вибору .exe файлу та завантажує конфігурацію.
        /// </summary>
        private bool SelectAndLoadJarvisPath()
        {
            using (OpenFileDialog ofd = new OpenFileDialog())
            {
                ofd.Filter = "Jarvis Executable (*.exe)|*.exe|All Files (*.*)|*.*";
                ofd.Title = "Виберіть виконуваний файл Jarvis";

                if (ofd.ShowDialog() == DialogResult.OK)
                {
                    SetJarvisPaths(ofd.FileName);

                    // Зберігаємо шлях у налаштуваннях програми
                    Properties.Settings.Default.JarvisPath = _jarvisExePath;
                    Properties.Settings.Default.Save();

                    LoadConfiguration();
                    return true;
                }
            }
            return false;
        }

        /// <summary>
        /// Встановлює внутрішні шляхи та оновлює UI.
        /// </summary>
        private void SetJarvisPaths(string exePath)
        {
            _jarvisExePath = exePath;
            string jarvisDir = Path.GetDirectoryName(_jarvisExePath);
            _configPath = Path.Combine(jarvisDir, ConfigFileName);

            lblJarvisPath.Text = _jarvisExePath;
        }

        /// <summary>
        /// Завантажує config.json та заповнює форму.
        /// </summary>
        private void LoadConfiguration()
        {
            if (string.IsNullOrEmpty(_configPath))
            {
                MessageBox.Show("Шлях до Jarvis не вибрано.", "Помилка",
                    MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            JarvisConfig config;

            if (!File.Exists(_configPath))
            {
                // Файл не знайдено, показуємо помилку та створюємо новий
                MessageBox.Show(
                    $"Файл конфігурації не знайдено за шляхом:\n{_configPath}\n\n" +
                    "Буде створено новий файл зі стандартними налаштуваннями.",
                    "Помилка конфігурації",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning);

                config = CreateDefaultConfig();
            }
            else
            {
                try
                {
                    // Створюємо опції, щоб ігнорувати регістр
                    var options = new JsonSerializerOptions
                    {
                        PropertyNameCaseInsensitive = true
                    };

                    string json = File.ReadAllText(_configPath);
                    config = JsonSerializer.Deserialize<JarvisConfig>(json, options);
                }
                catch (Exception ex)
                {
                    MessageBox.Show(
                        $"Не вдалося прочитати або розпізнати config.json:\n{ex.Message}\n\n" +
                        "Буде використано стандартні налаштування.",
                        "Помилка",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error);

                    config = new JarvisConfig();
                }
            }

            PopulateForm(config);
        }

        /// <summary>
        /// Створює, зберігає та повертає конфігурацію за замовчуванням.
        /// </summary>
        private JarvisConfig CreateDefaultConfig()
        {
            JarvisConfig defaultConfig = new JarvisConfig();

            try
            {
                var options = new JsonSerializerOptions
                {
                    WriteIndented = true,
                    PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                };

                string json = JsonSerializer.Serialize(defaultConfig, options);
                File.WriteAllText(_configPath, json);
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    $"Не вдалося створити новий файл конфігурації:\n{ex.Message}",
                    "Помилка запису",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error);
            }

            return defaultConfig;
        }

        /// <summary>
        /// Заповнює всі поля форми на основі завантаженого об'єкта конфігурації.
        /// </summary>
        private void PopulateForm(JarvisConfig config)
        {
            txtPicovoiceKey.Text = config.PicovoiceAccessKey;

            // Wake Word
            if (config.WakeWordMode == "custom")
                radioCustom.Checked = true;
            else
                radioStandard.Checked = true;

            cmbWakeWord.SelectedItem = config.WakeWordStandard;
            txtCustomWakeWordPath.Text = config.CustomWakeWordPath;

            // Чутливість
            trackSensitivity.Value = (int)Math.Round(config.Sensitivity * 100);
            UpdateSensitivityLabel();

            // Мова видалена - тепер багатомовний режим автоматично

            // Таймінги
            numCommandSessionTimeout.Value = Math.Max(numCommandSessionTimeout.Minimum,
                Math.Min(config.CommandSessionTimeout, numCommandSessionTimeout.Maximum));

            numContinuousListenSeconds.Value = Math.Max(numContinuousListenSeconds.Minimum,
                Math.Min(config.ContinuousListenSeconds, numContinuousListenSeconds.Maximum));

            numSilenceDetectSeconds.Value = (decimal)Math.Max((double)numSilenceDetectSeconds.Minimum,
                Math.Min(config.SilenceDetectSeconds, (double)numSilenceDetectSeconds.Maximum));
        }

        #endregion

        #region 2. Збереження та перезапуск

        /// <summary>
        /// Збирає дані з форми в об'єкт JarvisConfig.
        /// </summary>
        private JarvisConfig GatherDataFromForm()
        {
            return new JarvisConfig
            {
                PicovoiceAccessKey = txtPicovoiceKey.Text,
                WakeWordMode = radioStandard.Checked ? "standard" : "custom",
                WakeWordStandard = cmbWakeWord.SelectedItem?.ToString() ?? "jarvis",
                CustomWakeWordPath = txtCustomWakeWordPath.Text,
                Sensitivity = (double)trackSensitivity.Value / 100.0,
                // Language видалено - багатомовний режим автоматично
                CommandSessionTimeout = (int)numCommandSessionTimeout.Value,
                ContinuousListenSeconds = (int)numContinuousListenSeconds.Value,
                SilenceDetectSeconds = (double)numSilenceDetectSeconds.Value
            };
        }

        /// <summary>
        /// Зберігає поточні налаштування з форми в config.json.
        /// </summary>
        private bool SaveConfiguration()
        {
            if (string.IsNullOrEmpty(_configPath))
            {
                MessageBox.Show("Шлях до Jarvis не вибрано. Спочатку виберіть .exe файл.",
                    "Помилка", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return false;
            }

            try
            {
                JarvisConfig config = GatherDataFromForm();

                var options = new JsonSerializerOptions
                {
                    WriteIndented = true,
                    PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                };

                string json = JsonSerializer.Serialize(config, options);
                File.WriteAllText(_configPath, json);
                return true;
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Не вдалося зберегти config.json:\n{ex.Message}",
                    "Помилка запису", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return false;
            }
        }

        /// <summary>
        /// Перезапускає процес Jarvis.
        /// </summary>
        private void RestartJarvis()
        {
            if (string.IsNullOrEmpty(_jarvisExePath) || !File.Exists(_jarvisExePath))
            {
                MessageBox.Show("Неможливо перезапустити Jarvis: шлях до .exe файлу не знайдено.",
                    "Помилка", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }

            try
            {
                string processName = Path.GetFileNameWithoutExtension(_jarvisExePath);

                // 1. Завершуємо всі існуючі процеси Jarvis
                foreach (var process in Process.GetProcessesByName(processName))
                {
                    process.Kill();
                    process.WaitForExit(5000);
                }

                // 2. Запускаємо новий процес
                ProcessStartInfo startInfo = new ProcessStartInfo(_jarvisExePath)
                {
                    WorkingDirectory = Path.GetDirectoryName(_jarvisExePath)
                };

                Process.Start(startInfo);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Помилка під час перезапуску Jarvis:\n{ex.Message}",
                    "Помилка перезапуску", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        #endregion

        #region 3. Обробники подій елементів UI

        private void BtnSelectJarvis_Click(object sender, EventArgs e)
        {
            SelectAndLoadJarvisPath();
        }

        private void BtnSave_Click(object sender, EventArgs e)
        {
            if (SaveConfiguration())
            {
                MessageBox.Show("Конфігурацію збережено!", "Успіх",
                    MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
        }

        private void BtnSaveAndRestart_Click(object sender, EventArgs e)
        {
            if (SaveConfiguration())
            {
                RestartJarvis();
                MessageBox.Show("Jarvis перезапущено з новими налаштуваннями!", "Успіх",
                    MessageBoxButtons.OK, MessageBoxIcon.Information);
            }
        }

        private void BtnManageCommands_Click(object sender, EventArgs e)
        {
            if (_isCommandsMode)
            {
                // Якщо ми в режимі команд, повертаємося до налаштувань
                SwitchToSettingsMode();
                return;
            }

            if (string.IsNullOrEmpty(_jarvisExePath))
            {
                MessageBox.Show("Будь ласка, спочатку виберіть шлях до Jarvis.",
                    "Помилка", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            string jarvisDir = Path.GetDirectoryName(_jarvisExePath);
            _commandsPath = Path.Combine(jarvisDir, "commands");

            // Перевіряємо чи існує папка commands
            if (!Directory.Exists(_commandsPath))
            {
                var result = MessageBox.Show(
                    $"Папка 'commands' не знайдена за шляхом:\n{_commandsPath}\n\n" +
                    "Бажаєте створити її?",
                    "Папка команд не знайдена",
                    MessageBoxButtons.YesNo,
                    MessageBoxIcon.Question);

                if (result == DialogResult.Yes)
                {
                    try
                    {
                        Directory.CreateDirectory(_commandsPath);
                        MessageBox.Show("Папка 'commands' успішно створена.", "Успіх",
                            MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show($"Не вдалося створити папку:\n{ex.Message}",
                            "Помилка", MessageBoxButtons.OK, MessageBoxIcon.Error);
                        return;
                    }
                }
                else
                {
                    return;
                }
            }

            // Переключаємося в режим управління командами
            SwitchToCommandsMode();
        }

        private void BtnPicovoiceHelp_Click(object sender, EventArgs e)
        {
            OpenUrl("https://console.picovoice.ai/");
        }

        private void BtnPicovoiceWebsite_Click(object sender, EventArgs e)
        {
            OpenUrl("https://console.picovoice.ai/");
        }

        private void RadioWakeWord_CheckedChanged(object sender, EventArgs e)
        {
            UpdateWakeWordControls();
        }

        private void BtnBrowseCustomWakeWord_Click(object sender, EventArgs e)
        {
            using (OpenFileDialog ofd = new OpenFileDialog())
            {
                ofd.Filter = "Picovoice Wake Word (*.ppn)|*.ppn|All Files (*.*)|*.*";
                ofd.Title = "Виберіть файл моделі Wake Word";

                if (ofd.ShowDialog() == DialogResult.OK)
                {
                    txtCustomWakeWordPath.Text = ofd.FileName;
                }
            }
        }

        private void TrackSensitivity_Scroll(object sender, EventArgs e)
        {
            UpdateSensitivityLabel();
        }

        #endregion

        #region 4. Допоміжні методи

        /// <summary>
        /// Оновлює текст лейбла чутливості.
        /// </summary>
        private void UpdateSensitivityLabel()
        {
            double sensitivity = (double)trackSensitivity.Value / 100.0;
            lblSensitivityValue.Text = sensitivity.ToString("F2");
        }

        /// <summary>
        /// Оновлює доступність контролів Wake Word на основі RadioButton.
        /// </summary>
        private void UpdateWakeWordControls()
        {
            bool standard = radioStandard.Checked;
            cmbWakeWord.Enabled = standard;

            bool custom = radioCustom.Checked;
            txtCustomWakeWordPath.Enabled = custom;
            btnBrowseCustomWakeWord.Enabled = custom;
        }

        /// <summary>
        /// Безпечно відкриває URL у браузері за замовчуванням.
        /// </summary>
        private void OpenUrl(string url)
        {
            try
            {
                Process.Start(url);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Не вдалося відкрити браузер:\n{ex.Message}",
                    "Помилка", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        #endregion

        #region 5. Управління командами

        /// <summary>
        /// Переключає інтерфейс в режим управління командами
        /// </summary>
        private void SwitchToCommandsMode()
        {
            _isCommandsMode = true;

            // Змінюємо заголовок
            lblTitle.Text = "📋 УПРАВЛІННЯ КОМАНДАМИ";
            lblSubtitle.Text = "Перегляд та редагування голосових команд асистента";

            // Змінюємо текст кнопки футера
            btnManageCommands.Text = "⚙️ Налаштування";

            // Приховуємо панелі налаштувань
            panelLeft.Visible = false;
            panelRight.Visible = false;

            // Завантажуємо команди
            LoadCommands();

            // Показуємо панелі команд (створимо їх один раз)
            ShowCommandsPanels();
        }

        /// <summary>
        /// Показує панелі команд (створює їх один раз)
        /// </summary>
        private void ShowCommandsPanels()
        {
            // Створюємо панелі команд один раз, якщо їх ще немає
            if (_commandsLeftPanel == null)
            {
                CreateCommandsPanelsOnce();
            }

            // Приховуємо поточні панелі команд (якщо вони показані)
            HideCommandsPanels();

            // Оновлюємо список команд
            RefreshCommandsList();

            // Показуємо панелі команд
            panelMain.Controls.Add(_commandsLeftPanel);
            panelMain.Controls.Add(_commandsRightPanel);
        }

        /// <summary>
        /// Приховує панелі команд
        /// </summary>
        private void HideCommandsPanels()
        {
            if (_commandsLeftPanel != null && panelMain.Controls.Contains(_commandsLeftPanel))
            {
                panelMain.Controls.Remove(_commandsLeftPanel);
            }
            if (_commandsRightPanel != null && panelMain.Controls.Contains(_commandsRightPanel))
            {
                panelMain.Controls.Remove(_commandsRightPanel);
            }
        }

        /// <summary>
        /// Повертає інтерфейс в режим налаштувань
        /// </summary>
        private void SwitchToSettingsMode()
        {
            _isCommandsMode = false;

            // Відновлюємо заголовок
            lblTitle.Text = "⚡ ALEXA SETTINGS";
            lblSubtitle.Text = "Професійна конфігурація голосового асистента";

            // Відновлюємо текст кнопки
            btnManageCommands.Text = "📋 Управління командами";

            // Приховуємо панелі команд
            HideCommandsPanels();

            // Показуємо панелі налаштувань
            panelLeft.Visible = true;
            panelRight.Visible = true;
        }

        /// <summary>
        /// Завантажує команди з папки commands
        /// </summary>
        private void LoadCommands()
        {
            _loadedCommands.Clear();

            if (!Directory.Exists(_commandsPath))
                return;

            try
            {
                var commandFiles = Directory.GetFiles(_commandsPath, "*_command.json");

                foreach (var filePath in commandFiles)
                {
                    try
                    {
                        string json = File.ReadAllText(filePath);
                        var command = JsonSerializer.Deserialize<VoiceCommand>(json, new JsonSerializerOptions
                        {
                            PropertyNameCaseInsensitive = true
                        });

                        if (command != null)
                        {
                            command.FileName = Path.GetFileName(filePath);
                            _loadedCommands.Add(command);
                        }
                    }
                    catch (Exception ex)
                    {
                        MessageBox.Show($"Помилка завантаження команди з файлу {Path.GetFileName(filePath)}:\n{ex.Message}",
                            "Помилка", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    }
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Помилка читання папки команд:\n{ex.Message}",
                    "Помилка", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }


        /// <summary>
        /// Створює панель з кнопкою повернення
        /// </summary>
        private Panel CreateBackButtonPanel()
        {
            var panel = new Panel
            {
                BackColor = Color.FromArgb(45, 50, 55),
                Dock = DockStyle.Top,
                Height = 60,
                Padding = new Padding(15)
            };

            var backButton = new Button
            {
                Text = "◀ Повернутися до налаштувань",
                BackColor = Color.FromArgb(70, 80, 90),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Segoe UI Semibold", 9F, FontStyle.Bold),
                Size = new Size(250, 32),
                Location = new Point(15, 14),
                Cursor = Cursors.Hand
            };

            backButton.FlatAppearance.BorderSize = 0;
            backButton.Click += (s, e) => SwitchToSettingsMode();
            backButton.MouseEnter += Button_MouseEnter;
            backButton.MouseLeave += Button_MouseLeave;

            panel.Controls.Add(backButton);
            return panel;
        }

        /// <summary>
        /// Створює панель зі списком команд
        /// </summary>
        private Panel CreateCommandsListPanel()
        {
            var panel = new Panel
            {
                BackColor = Color.FromArgb(45, 50, 55),
                Dock = DockStyle.Fill,
                Padding = new Padding(15)
            };

            var titleLabel = new Label
            {
                Text = "📋 Список команд",
                Font = new Font("Segoe UI Semibold", 12F, FontStyle.Bold),
                ForeColor = Color.FromArgb(242, 242, 247),
                AutoSize = true,
                Location = new Point(15, 10)
            };

            var newCommandButton = new Button
            {
                Text = "➕ Нова команда",
                BackColor = Color.FromArgb(95, 135, 165),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Segoe UI Semibold", 9F, FontStyle.Bold),
                Size = new Size(150, 30),
                Anchor = AnchorStyles.Top | AnchorStyles.Right,
                Cursor = Cursors.Hand
            };

            // Розташовуємо кнопку праворуч від заголовка
            newCommandButton.Location = new Point(panel.Width - 165, 8);

            newCommandButton.FlatAppearance.BorderSize = 0;
            newCommandButton.MouseEnter += Button_MouseEnter;
            newCommandButton.MouseLeave += Button_MouseLeave;
            newCommandButton.Click += (s, e) => CreateNewCommand();

            var listView = new ListView
            {
                View = View.Details,
                FullRowSelect = true,
                GridLines = true,
                BackColor = Color.FromArgb(60, 65, 70),
                ForeColor = Color.FromArgb(242, 242, 247),
                BorderStyle = BorderStyle.None,
                Font = new Font("Segoe UI", 9F),
                Location = new Point(15, 40),
                Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right | AnchorStyles.Bottom
            };

            // Встановлюємо правильний розмір відносно панелі
            listView.Size = new Size(panel.Width - 30, panel.Height - 55);

            // Додаємо колонки з адаптивною шириною
            int totalWidth = listView.Width - 20; // Віднімаємо для margin
            listView.Columns.Add("Назва", (int)(totalWidth * 0.25)); // 25%
            listView.Columns.Add("Тип", (int)(totalWidth * 0.15)); // 15%
            listView.Columns.Add("Фрази", (int)(totalWidth * 0.40)); // 40%
            listView.Columns.Add("Файл", (int)(totalWidth * 0.20)); // 20%

            // Заповнюємо команди
            foreach (var command in _loadedCommands)
            {
                var item = new ListViewItem(command.Name);
                item.SubItems.Add(command.DisplayType); // Використовуємо DisplayType замість Type
                item.SubItems.Add(string.Join(", ", command.Phrases.Take(2))); // Показуємо перші 2 фрази
                item.SubItems.Add(command.FileName);
                item.Tag = command;
                listView.Items.Add(item);
            }

            // Додаємо обробник вибору команди
            listView.SelectedIndexChanged += (sender, e) =>
            {
                if (listView.SelectedItems.Count > 0)
                {
                    var selectedCommand = (VoiceCommand)listView.SelectedItems[0].Tag;
                    ShowCommandDetails(selectedCommand);
                }
            };

            // Додаємо обробник зміни розміру для адаптації колонок
            panel.Resize += (sender, e) =>
            {
                if (listView.Columns.Count > 0)
                {
                    int resizedWidth = listView.Width - 20;
                    listView.Columns[0].Width = (int)(resizedWidth * 0.25); // Назва
                    listView.Columns[1].Width = (int)(resizedWidth * 0.15); // Тип
                    listView.Columns[2].Width = (int)(resizedWidth * 0.40); // Фрази
                    listView.Columns[3].Width = (int)(resizedWidth * 0.20); // Файл
                }
            };

            panel.Controls.Add(titleLabel);
            panel.Controls.Add(newCommandButton);
            panel.Controls.Add(listView);

            return panel;
        }

        /// <summary>
        /// Створює панель для деталей команди
        /// </summary>
        private Panel CreateCommandDetailsPanel()
        {
            var panel = new Panel
            {
                BackColor = Color.FromArgb(45, 50, 55),
                Dock = DockStyle.Fill,
                Padding = new Padding(15),
                AutoScroll = true, // Додаємо автоскролінг
                Name = "commandDetailsPanel" // Даємо ім'я для пошуку
            };

            var titleLabel = new Label
            {
                Text = "📝 Деталі команди",
                Font = new Font("Segoe UI Semibold", 12F, FontStyle.Bold),
                ForeColor = Color.FromArgb(242, 242, 247),
                AutoSize = true,
                Location = new Point(15, 10)
            };

            var infoLabel = new Label
            {
                Text = "Виберіть команду зі списку для перегляду деталей.",
                Font = new Font("Segoe UI", 9F),
                ForeColor = Color.FromArgb(142, 142, 147),
                Location = new Point(15, 50),
                AutoSize = true,
                Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right,
                Name = "commandInfoLabel"
            };

            panel.Controls.Add(titleLabel);
            panel.Controls.Add(infoLabel);

            return panel;
        }

        /// <summary>
        /// Відображає деталі вибраної команди
        /// </summary>
        private void ShowCommandDetails(VoiceCommand command)
        {
            // Знаходимо панель деталей
            var detailsPanel = panelRight.Controls.Find("commandDetailsPanel", true).FirstOrDefault() as Panel;
            if (detailsPanel == null) return;

            // Очищуємо поточний контент (крім заголовка)
            var titleLabel = detailsPanel.Controls[0]; // Зберігаємо заголовок
            detailsPanel.Controls.Clear();
            detailsPanel.Controls.Add(titleLabel);

            int yPos = 50;

            // Назва команди
            AddDetailField(detailsPanel, "📌 Назва:", command.Name, ref yPos);

            // Тип команди
            AddDetailField(detailsPanel, "🔧 Тип:", command.DisplayType, ref yPos);

            // Для стандартних команд показуємо ціль
            if (!command.IsCombinedCommand)
            {
                AddDetailField(detailsPanel, "🎯 Ціль:", command.Target ?? "null", ref yPos);
            }
            else
            {
                // Для комбінованих команд показуємо дії
                var actionsLabel = new Label
                {
                    Text = "🔗 Дії в комбінації:",
                    Font = new Font("Segoe UI Semibold", 9F, FontStyle.Bold),
                    ForeColor = Color.FromArgb(242, 242, 247),
                    AutoSize = true,
                    Location = new Point(15, yPos)
                };
                detailsPanel.Controls.Add(actionsLabel);
                yPos += 25;

                // Показуємо кожну дію
                for (int i = 0; i < command.Actions.Count; i++)
                {
                    var action = command.Actions[i];
                    var actionLabel = new Label
                    {
                        Text = $"{i + 1}. {GetActionTypeDisplay(action.Type)} → {action.Target ?? "системна дія"}",
                        Font = new Font("Segoe UI", 9F),
                        ForeColor = Color.FromArgb(200, 200, 200),
                        AutoSize = true,
                        MaximumSize = new Size(detailsPanel.Width - 60, 0), // Обмежуємо ширину
                        Location = new Point(30, yPos)
                    };
                    detailsPanel.Controls.Add(actionLabel);
                    yPos += 20;
                }
                yPos += 10;
            }

            // Потребує аргументи
            AddDetailField(detailsPanel, "⚙️ Потребує аргументи:", command.RequiresArgument ? "Так" : "Ні", ref yPos);

            // Фрази активації
            var phrasesLabel = new Label
            {
                Text = "🎤 Фрази активації:",
                Font = new Font("Segoe UI Semibold", 9F, FontStyle.Bold),
                ForeColor = Color.FromArgb(242, 242, 247),
                AutoSize = true,
                Location = new Point(15, yPos)
            };
            detailsPanel.Controls.Add(phrasesLabel);
            yPos += 25;

            // Список фраз
            foreach (var phrase in command.Phrases)
            {
                var phraseLabel = new Label
                {
                    Text = $"• \"{phrase}\"",
                    Font = new Font("Segoe UI", 9F),
                    ForeColor = Color.FromArgb(200, 200, 200),
                    AutoSize = true,
                    MaximumSize = new Size(detailsPanel.Width - 60, 0), // Обмежуємо ширину
                    Location = new Point(30, yPos)
                };
                detailsPanel.Controls.Add(phraseLabel);
                yPos += 20;
            }

            yPos += 10;

            // Ім'я файлу
            AddDetailField(detailsPanel, "📁 Файл:", command.FileName, ref yPos);

            // Кнопки дій
            yPos += 20;
            var editButton = new Button
            {
                Text = "✏️ Редагувати",
                BackColor = Color.FromArgb(95, 135, 165),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Segoe UI Semibold", 9F, FontStyle.Bold),
                Size = new Size(120, 30),
                Location = new Point(15, yPos),
                Cursor = Cursors.Hand
            };
            editButton.FlatAppearance.BorderSize = 0;
            editButton.MouseEnter += Button_MouseEnter;
            editButton.MouseLeave += Button_MouseLeave;
            editButton.Click += (s, e) => EditCommand(command);

            var deleteButton = new Button
            {
                Text = "🗑️ Видалити",
                BackColor = Color.FromArgb(180, 70, 70),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Segoe UI Semibold", 9F, FontStyle.Bold),
                Size = new Size(120, 30),
                Location = new Point(145, yPos),
                Cursor = Cursors.Hand
            };
            deleteButton.FlatAppearance.BorderSize = 0;
            deleteButton.MouseEnter += Button_MouseEnter;
            deleteButton.MouseLeave += Button_MouseLeave;
            deleteButton.Click += (s, e) => DeleteCommand(command);

            detailsPanel.Controls.Add(editButton);
            detailsPanel.Controls.Add(deleteButton);
        }

        /// <summary>
        /// Повертає красиве відображення типу дії
        /// </summary>
        private string GetActionTypeDisplay(string actionType)
        {
            switch (actionType.ToLower())
            {
                case "website":
                    return "🌐 Веб-сайт";
                case "application":
                    return "🚀 Програма";
                case "script":
                    return "📜 Скрипт";
                case "system_volume":
                    return "🔊 Гучність системи";
                case "app_volume":
                    return "🎵 Гучність програми";
                default:
                    return $"❓ {actionType}";
            }
        }

        /// <summary>
        /// Додає поле деталей до панелі
        /// </summary>
        private void AddDetailField(Panel panel, string label, string value, ref int yPos)
        {
            var labelControl = new Label
            {
                Text = label,
                Font = new Font("Segoe UI Semibold", 9F, FontStyle.Bold),
                ForeColor = Color.FromArgb(242, 242, 247),
                AutoSize = true,
                Location = new Point(15, yPos)
            };

            var valueControl = new Label
            {
                Text = value,
                Font = new Font("Segoe UI", 9F),
                ForeColor = Color.FromArgb(200, 200, 200),
                AutoSize = true,
                MaximumSize = new Size(panel.Width - 40, 0), // Обмежуємо ширину для переносу тексту
                Location = new Point(15, yPos + 18)
            };

            panel.Controls.Add(labelControl);
            panel.Controls.Add(valueControl);

            yPos += 45;
        }

        /// <summary>
        /// Редагування команди (заглушка)
        /// </summary>
        private void EditCommand(VoiceCommand command)
        {
            MessageBox.Show($"Редагування команди '{command.Name}' буде реалізовано в наступній версії.",
                "Функція в розробці", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        /// <summary>
        /// Видалення команди
        /// </summary>
        private void DeleteCommand(VoiceCommand command)
        {
            var result = MessageBox.Show(
                $"Ви впевнені, що хочете видалити команду '{command.Name}'?\n\nФайл: {command.FileName}",
                "Підтвердження видалення",
                MessageBoxButtons.YesNo,
                MessageBoxIcon.Question);

            if (result == DialogResult.Yes)
            {
                try
                {
                    string filePath = Path.Combine(_commandsPath, command.FileName);
                    if (File.Exists(filePath))
                    {
                        File.Delete(filePath);
                        MessageBox.Show($"Команду '{command.Name}' успішно видалено.",
                            "Успіх", MessageBoxButtons.OK, MessageBoxIcon.Information);

                        // Перезавантажуємо команди та оновлюємо UI
                        LoadCommands();
                        RefreshCommandsList();
                    }
                    else
                    {
                        MessageBox.Show($"Файл {command.FileName} не знайдено.",
                            "Помилка", MessageBoxButtons.OK, MessageBoxIcon.Error);
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Помилка видалення команди:\n{ex.Message}",
                        "Помилка", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
        }

        /// <summary>
        /// Створює нову команду з вибором типу
        /// </summary>
        private void CreateNewCommand()
        {
            var choiceDialog = MessageBox.Show(
                "Оберіть тип команди:\n\n" +
                "• Так - Проста команда (одна дія)\n" +
                "• Ні - Комбінована команда (кілька дій)\n" +
                "• Скасувати - Вибрати з готових шаблонів",
                "Тип нової команди",
                MessageBoxButtons.YesNoCancel,
                MessageBoxIcon.Question);

            switch (choiceDialog)
            {
                case DialogResult.Yes:
                    CreateSimpleCommandTemplate();
                    break;
                case DialogResult.No:
                    CreateCombinedCommandTemplate();
                    break;
                case DialogResult.Cancel:
                    ShowCommandTemplates();
                    break;
            }
        }

        /// <summary>
        /// Створює шаблон простої команди
        /// </summary>
        private void CreateSimpleCommandTemplate()
        {
            var simpleTemplate = new VoiceCommand
            {
                Name = "my_new_command",
                Phrases = new List<string> { "моя команда", "виконай дію" },
                Type = "website",
                Target = "https://www.google.com",
                RequiresArgument = false
            };

            SaveCommandTemplate(simpleTemplate, "simple_command");
        }

        /// <summary>
        /// Створює шаблон комбінованої команди
        /// </summary>
        private void CreateCombinedCommandTemplate()
        {
            var combinedTemplate = new VoiceCommand
            {
                Name = "my_combined_command",
                Phrases = new List<string> { "робочий режим", "режим роботи" },
                Actions = new List<CommandAction>
                {
                    new CommandAction { Type = "application", Target = "notepad.exe" },
                    new CommandAction { Type = "website", Target = "https://www.google.com" },
                    new CommandAction { Type = "system_volume", Target = null }
                },
                RequiresArgument = true
            };

            SaveCommandTemplate(combinedTemplate, "combined_command");
        }

        /// <summary>
        /// Показує готові шаблони команд
        /// </summary>
        private void ShowCommandTemplates()
        {
            var templates = new[]
            {
                "1. Відкрити YouTube",
                "2. Ігровий режим (Steam + Discord)",
                "3. Робочий режим (Office + Teams)",
                "4. Режим розробки (VS Code + GitHub)",
                "5. Вечірня рутина (Spotify + Netflix)"
            };

            var choice = MessageBox.Show(
                "Оберіть готовий шаблон:\n\n" + string.Join("\n", templates) + "\n\nВведіть номер від 1 до 5:",
                "Шаблони команд",
                MessageBoxButtons.OKCancel,
                MessageBoxIcon.Information);

            if (choice == DialogResult.OK)
            {
                // Для простоти використаємо послідовні діалоги
                var templateChoice = MessageBox.Show(
                    "Оберіть:\n\n" +
                    "Так - Шаблони 1-2 (YouTube, Ігровий режим)\n" +
                    "Ні - Шаблони 3-5 (Робота, Розробка, Відпочинок)",
                    "Група шаблонів",
                    MessageBoxButtons.YesNoCancel,
                    MessageBoxIcon.Question);

                if (templateChoice == DialogResult.Yes)
                {
                    var choice12 = MessageBox.Show(
                        "Так - YouTube\nНі - Ігровий режим",
                        "Шаблон 1-2",
                        MessageBoxButtons.YesNo,
                        MessageBoxIcon.Question);
                    CreateTemplateCommand(choice12 == DialogResult.Yes ? 1 : 2);
                }
                else if (templateChoice == DialogResult.No)
                {
                    var choice345 = MessageBox.Show(
                        "Оберіть:\n\n" +
                        "Так - Робочий режим\n" +
                        "Ні - Режим розробки\n" +
                        "Скасувати - Вечірня рутина",
                        "Шаблон 3-5",
                        MessageBoxButtons.YesNoCancel,
                        MessageBoxIcon.Question);

                    int templateNum = 0;
                    if (choice345 == DialogResult.Yes)
                        templateNum = 3;
                    else if (choice345 == DialogResult.No)
                        templateNum = 4;
                    else if (choice345 == DialogResult.Cancel)
                        templateNum = 5;

                    if (templateNum > 0)
                        CreateTemplateCommand(templateNum);
                }
            }
        }

        /// <summary>
        /// Створює команду з готового шаблону
        /// </summary>
        private void CreateTemplateCommand(int templateNumber)
        {
            VoiceCommand template = null;

            switch (templateNumber)
            {
                case 1:
                    template = new VoiceCommand
                    {
                        Name = "open_youtube",
                        Phrases = new List<string> { "відкрий ютуб", "запусти youtube" },
                        Type = "website",
                        Target = "https://www.youtube.com",
                        RequiresArgument = false
                    };
                    break;
                case 2:
                    template = new VoiceCommand
                    {
                        Name = "gaming_setup",
                        Phrases = new List<string> { "ігровий режим", "підготуй до гри" },
                        Actions = new List<CommandAction>
                        {
                            new CommandAction { Type = "system_volume", Target = null },
                            new CommandAction { Type = "application", Target = "C:\\Program Files (x86)\\Steam\\steam.exe" },
                            new CommandAction { Type = "application", Target = "C:\\Program Files\\Discord\\Discord.exe" }
                        },
                        RequiresArgument = true
                    };
                    break;
                case 3:
                    template = new VoiceCommand
                    {
                        Name = "work_mode",
                        Phrases = new List<string> { "робочий режим", "час працювати" },
                        Actions = new List<CommandAction>
                        {
                            new CommandAction { Type = "application", Target = "outlook.exe" },
                            new CommandAction { Type = "application", Target = "teams.exe" },
                            new CommandAction { Type = "website", Target = "https://calendar.google.com" }
                        },
                        RequiresArgument = false
                    };
                    break;
                case 4:
                    template = new VoiceCommand
                    {
                        Name = "dev_setup",
                        Phrases = new List<string> { "режим розробки", "почати кодити" },
                        Actions = new List<CommandAction>
                        {
                            new CommandAction { Type = "application", Target = "code.exe" },
                            new CommandAction { Type = "website", Target = "https://github.com" },
                            new CommandAction { Type = "website", Target = "https://stackoverflow.com" }
                        },
                        RequiresArgument = false
                    };
                    break;
                case 5:
                    template = new VoiceCommand
                    {
                        Name = "evening_routine",
                        Phrases = new List<string> { "вечірній режим", "час відпочинку" },
                        Actions = new List<CommandAction>
                        {
                            new CommandAction { Type = "application", Target = "spotify.exe" },
                            new CommandAction { Type = "website", Target = "https://www.netflix.com" }
                        },
                        RequiresArgument = false
                    };
                    break;
            }

            if (template != null)
            {
                SaveCommandTemplate(template, $"template_{templateNumber}_command");
            }
        }

        /// <summary>
        /// Зберігає шаблон команди у файл
        /// </summary>
        private void SaveCommandTemplate(VoiceCommand command, string baseFileName)
        {
            try
            {
                string fileName = $"{baseFileName}_command.json";
                string filePath = Path.Combine(_commandsPath, fileName);

                // Перевіряємо чи файл вже існує
                int counter = 1;
                while (File.Exists(filePath))
                {
                    fileName = $"{baseFileName}_{counter}_command.json";
                    filePath = Path.Combine(_commandsPath, fileName);
                    counter++;
                }

                var options = new JsonSerializerOptions
                {
                    WriteIndented = true,
                    PropertyNamingPolicy = JsonNamingPolicy.CamelCase
                };

                string json = JsonSerializer.Serialize(command, options);
                File.WriteAllText(filePath, json);

                MessageBox.Show(
                    $"Шаблон команди створено!\n\n" +
                    $"Файл: {fileName}\n" +
                    $"Назва: {command.Name}\n\n" +
                    "Тепер ви можете відредагувати файл у текстовому редакторі.",
                    "Команда створена",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information);

                // Перезавантажуємо команди та оновлюємо UI
                LoadCommands();
                RefreshCommandsList();
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Помилка створення команди:\n{ex.Message}",
                    "Помилка", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        /// <summary>
        /// Відновлює оригінальний UI налаштувань
        /// </summary>
        private void RestoreOriginalUI()
        {
            // Очищуємо поточний контент панелей команд
            panelLeft.Controls.Clear();
            panelRight.Controls.Clear();

            // Відновлюємо оригінальні панелі через Designer без очищення всієї форми
            RestoreOriginalControls();

            // Якщо є збережені налаштування, завантажуємо їх
            if (!string.IsNullOrEmpty(_jarvisExePath))
            {
                SetJarvisPaths(_jarvisExePath);
                LoadConfiguration();
            }
        }

        /// <summary>
        /// Відновлює оригінальні контроли налаштувань без порушення масштабування
        /// </summary>
        private void RestoreOriginalControls()
        {
            // Створюємо тимчасову форму для копіювання оригінальної структури
            var tempForm = new Form1();
            tempForm.InitializeComponent();

            // Копіюємо структуру панелей з тимчасової форми
            CopyPanelStructure(tempForm.panelLeft, panelLeft);
            CopyPanelStructure(tempForm.panelRight, panelRight);

            // Очищуємо тимчасову форму
            tempForm.Dispose();

            // Відновлюємо обробники подій
            InitializeEventHandlers();
        }

        /// <summary>
        /// Копіює структуру панелі з контролами
        /// </summary>
        private void CopyPanelStructure(Panel source, Panel target)
        {
            // Копіюємо всі дочірні контроли
            foreach (Control control in source.Controls)
            {
                target.Controls.Add(control);
            }
        }

        /// <summary>
        /// Створює панелі команд один раз і кешує їх для швидкого перемикання
        /// </summary>
        private void CreateCommandsPanelsOnce()
        {
            // Ліва панель (список команд)
            _commandsLeftPanel = new Panel
            {
                Name = "commandsLeftPanel",
                BackColor = Color.FromArgb(50, 60, 75),
                Size = new Size(400, panelMain.Height),
                Location = new Point(0, 0),
                Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left
            };

            // ListView для команд
            _commandsListView = new ListView
            {
                Name = "commandsListView",
                View = View.Details,
                FullRowSelect = true,
                GridLines = true,
                BackColor = Color.FromArgb(40, 50, 65),
                ForeColor = Color.White,
                BorderStyle = BorderStyle.None,
                HeaderStyle = ColumnHeaderStyle.Nonclickable,
                Location = new Point(20, 80),
                Size = new Size(360, panelMain.Height - 120),
                Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right
            };

            // Додаємо колонки до ListView
            _commandsListView.Columns.Add("Назва", 120);
            _commandsListView.Columns.Add("Тип", 80);
            _commandsListView.Columns.Add("Фрази", 140);

            // Обробник події для вибору команди
            _commandsListView.SelectedIndexChanged += CommandsListView_SelectedIndexChanged;

            // Заголовок для лівої панелі
            Label commandsTitle = new Label
            {
                Text = "📋 Список команд",
                Font = new Font("Segoe UI", 14, FontStyle.Bold),
                ForeColor = Color.White,
                Location = new Point(20, 20),
                Size = new Size(200, 30),
                BackColor = Color.Transparent
            };

            // Кнопки управління командами
            Button btnCreateCommand = new Button
            {
                Text = "➕ Створити",
                BackColor = Color.FromArgb(95, 135, 165),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Segoe UI", 9, FontStyle.Bold),
                Location = new Point(20, 50),
                Size = new Size(90, 25)
            };
            btnCreateCommand.FlatAppearance.BorderSize = 0;
            btnCreateCommand.Click += BtnCreateCommand_Click;

            Button btnDeleteCommand = new Button
            {
                Text = "🗑️ Видалити",
                BackColor = Color.FromArgb(180, 95, 95),
                ForeColor = Color.White,
                FlatStyle = FlatStyle.Flat,
                Font = new Font("Segoe UI", 9, FontStyle.Bold),
                Location = new Point(120, 50),
                Size = new Size(90, 25)
            };
            btnDeleteCommand.FlatAppearance.BorderSize = 0;
            btnDeleteCommand.Click += BtnDeleteCommand_Click;

            // Додаємо контроли до лівої панелі
            _commandsLeftPanel.Controls.Add(commandsTitle);
            _commandsLeftPanel.Controls.Add(btnCreateCommand);
            _commandsLeftPanel.Controls.Add(btnDeleteCommand);
            _commandsLeftPanel.Controls.Add(_commandsListView);

            // Права панель (деталі команди)
            _commandsRightPanel = new Panel
            {
                Name = "commandsRightPanel",
                BackColor = Color.FromArgb(45, 55, 70),
                Size = new Size(panelMain.Width - 400, panelMain.Height),
                Location = new Point(400, 0),
                Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right
            };

            // Панель для деталей команди
            _commandDetailsPanel = new Panel
            {
                Name = "commandDetailsPanel",
                BackColor = Color.FromArgb(45, 55, 70),
                Location = new Point(20, 20),
                Size = new Size(_commandsRightPanel.Width - 40, _commandsRightPanel.Height - 40),
                Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right
            };

            // Заголовок для правої панелі
            Label detailsTitle = new Label
            {
                Text = "📄 Деталі команди",
                Font = new Font("Segoe UI", 14, FontStyle.Bold),
                ForeColor = Color.White,
                Location = new Point(0, 0),
                Size = new Size(200, 30),
                BackColor = Color.Transparent
            };

            // Текстове поле для відображення деталей команди
            TextBox commandDetails = new TextBox
            {
                Name = "commandDetailsText",
                Multiline = true,
                ScrollBars = ScrollBars.Vertical,
                ReadOnly = true,
                BackColor = Color.FromArgb(35, 45, 60),
                ForeColor = Color.White,
                BorderStyle = BorderStyle.None,
                Font = new Font("Consolas", 10),
                Location = new Point(0, 40),
                Size = new Size(_commandDetailsPanel.Width, _commandDetailsPanel.Height - 40),
                Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right,
                Text = "Виберіть команду зі списку для перегляду деталей..."
            };

            _commandDetailsPanel.Controls.Add(detailsTitle);
            _commandDetailsPanel.Controls.Add(commandDetails);
            _commandsRightPanel.Controls.Add(_commandDetailsPanel);
        }

        /// <summary>
        /// Оновлює список команд без перестворення UI
        /// </summary>
        private void RefreshCommandsList()
        {
            if (_commandsListView == null)
                return;

            _commandsListView.Items.Clear();

            foreach (var command in _loadedCommands)
            {
                var item = new ListViewItem(command.Name);

                if (command.IsCombinedCommand)
                {
                    item.SubItems.Add("Комбінована");
                    item.SubItems.Add($"{command.Actions.Count} дій");
                }
                else
                {
                    item.SubItems.Add(command.Type);
                    item.SubItems.Add(string.Join(", ", command.Phrases));
                }

                item.Tag = command;
                _commandsListView.Items.Add(item);
            }

            // Автоматично підлаштовуємо ширину колонок
            foreach (ColumnHeader column in _commandsListView.Columns)
            {
                column.AutoResize(ColumnHeaderAutoResizeStyle.ColumnContent);
            }
        }

        /// <summary>
        /// Обробник зміни вибору в списку команд
        /// </summary>
        private void CommandsListView_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (_commandsListView.SelectedItems.Count == 0)
                return;

            var selectedCommand = (VoiceCommand)_commandsListView.SelectedItems[0].Tag;
            var detailsTextBox = _commandDetailsPanel.Controls["commandDetailsText"] as TextBox;

            if (detailsTextBox != null)
            {
                var options = new JsonSerializerOptions
                {
                    WriteIndented = true,
                    PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
                    Encoder = JavaScriptEncoder.UnsafeRelaxedJsonEscaping
                };

                detailsTextBox.Text = JsonSerializer.Serialize(selectedCommand, options);
            }
        }

        /// <summary>
        /// Обробник кнопки створення команди
        /// </summary>
        private void BtnCreateCommand_Click(object sender, EventArgs e)
        {
            CreateNewCommand();
        }

        /// <summary>
        /// Обробник кнопки видалення команди
        /// </summary>
        private void BtnDeleteCommand_Click(object sender, EventArgs e)
        {
            if (_commandsListView.SelectedItems.Count == 0)
            {
                MessageBox.Show("Будь ласка, виберіть команду для видалення.",
                    "Команда не вибрана", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }

            var selectedCommand = (VoiceCommand)_commandsListView.SelectedItems[0].Tag;
            DeleteCommand(selectedCommand);
        }

        #endregion

        private void Form1_Load_1(object sender, EventArgs e)
        {

        }

        private void lblJarvisPath_Click(object sender, EventArgs e)
        {

        }
    }
}