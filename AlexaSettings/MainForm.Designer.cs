namespace AlexaSettings
{
    partial class MainForm
    {
        private System.ComponentModel.IContainer components = null;

        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null)) components.Dispose();
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        private void InitializeComponent()
        {
            tabControl = new TabControl();
            tabMicrophone = new TabPage();
            tabTokens = new TabPage();
            tabWakeWord = new TabPage();
            tabModel = new TabPage();
            tabListening = new TabPage();
            tabSystem = new TabPage();

            // System tab
            chkAutostart = new CheckBox();
            lblAutostartHint = new Label();
            lblAutostartPath = new Label();

            // Microphone
            lblMicrophoneDesc = new Label();
            lblMicrophone = new Label();
            cmbMicrophone = new ComboBox();

            // Tokens
            lblPicovoiceKey = new Label();
            txtPicovoiceKey = new TextBox();
            lblPicovoiceKeyHint = new Label();
            lblOpenAiKey = new Label();
            txtOpenAiKey = new TextBox();
            lblOpenAiKeyHint = new Label();

            // WakeWord
            rbStandardWakeWord = new RadioButton();
            rbCustomWakeWord = new RadioButton();
            lblWakeWordStandardLabel = new Label();
            cmbWakeWordStandard = new ComboBox();
            lblCustomWakeWordPath = new Label();
            txtCustomWakeWordPath = new TextBox();
            btnBrowsePpn = new Button();
            lblCustomWakeWordHint = new Label();
            lblSensitivity = new Label();
            trackSensitivity = new TrackBar();
            lblSensitivityValue = new Label();
            lblSensitivityHint = new Label();

            // Model / TTS / Languages
            chkTtsEnabled = new CheckBox();
            lblTtsHint = new Label();
            lblTtsVoice = new Label();
            cmbTtsVoice = new ComboBox();
            lblTtsVoiceHint = new Label();
            lblTtsRate = new Label();
            txtTtsRate = new TextBox();
            lblTtsRateHint = new Label();
            lblLanguagesTitle = new Label();
            lblLanguagesHint = new Label();
            // Чекбокси мов — створюємо динамічно в LoadConfig, тут тільки Panel
            pnlLanguages = new FlowLayoutPanel();

            // Listening
            lblCommandTimeout = new Label();
            nudCommandTimeout = new NumericUpDown();
            lblCommandTimeoutHint = new Label();
            lblContinuousListen = new Label();
            nudContinuousListen = new NumericUpDown();
            lblContinuousListenHint = new Label();
            lblSilenceDetect = new Label();
            nudSilenceDetect = new NumericUpDown();
            lblSilenceDetectHint = new Label();
            lblSilenceTimeout = new Label();
            nudSilenceTimeout = new NumericUpDown();
            lblSilenceTimeoutHint = new Label();

            // Bottom
            btnSave = new Button();
            btnReload = new Button();
            lblConfigPath = new Label();

            tabControl.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)trackSensitivity).BeginInit();
            ((System.ComponentModel.ISupportInitialize)nudCommandTimeout).BeginInit();
            ((System.ComponentModel.ISupportInitialize)nudContinuousListen).BeginInit();
            ((System.ComponentModel.ISupportInitialize)nudSilenceDetect).BeginInit();
            ((System.ComponentModel.ISupportInitialize)nudSilenceTimeout).BeginInit();
            SuspendLayout();

            // ==============================
            // FORM
            // ==============================
            Text = "Alexa — Налаштування";
            ClientSize = new Size(600, 510);
            FormBorderStyle = FormBorderStyle.FixedSingle;
            MaximizeBox = false;
            StartPosition = FormStartPosition.CenterScreen;
            Font = new Font("Segoe UI", 9.5f);
            BackColor = Color.FromArgb(245, 245, 248);

            // ==============================
            // TAB CONTROL
            // ==============================
            tabControl.Location = new Point(10, 10);
            tabControl.Size = new Size(578, 450);
            tabControl.Font = new Font("Segoe UI", 9.5f);
            tabControl.TabPages.AddRange(new TabPage[] {
                tabMicrophone, tabTokens, tabWakeWord, tabModel, tabListening, tabSystem
            });

            tabMicrophone.Text = "  Мікрофон  ";
            tabTokens.Text = "  Токени  ";
            tabWakeWord.Text = "  Слово-тригер  ";
            tabModel.Text = "  Голос / ШІ  ";
            tabListening.Text = "  Слухання  ";
            tabSystem.Text = "  Система  ";

            foreach (TabPage tp in tabControl.TabPages)
                tp.BackColor = Color.FromArgb(250, 250, 253);

            int lx = 18;
            Color hintColor = Color.FromArgb(100, 100, 110);

            // ==============================
            // TAB: МІКРОФОН
            // ==============================
            lblMicrophoneDesc.Text = "Оберіть мікрофон, який буде слухати голосові команди.\nЯкщо залишити «За замовчуванням» — використовується мікрофон, вибраний у системі Windows.";
            lblMicrophoneDesc.Location = new Point(lx, 18);
            lblMicrophoneDesc.Size = new Size(530, 38);
            lblMicrophoneDesc.ForeColor = hintColor;

            lblMicrophone.Text = "Мікрофон:";
            lblMicrophone.Location = new Point(lx, 68);
            lblMicrophone.AutoSize = true;
            lblMicrophone.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);

            cmbMicrophone.Location = new Point(lx, 88);
            cmbMicrophone.Size = new Size(530, 26);
            cmbMicrophone.DropDownStyle = ComboBoxStyle.DropDownList;

            tabMicrophone.Controls.AddRange(new Control[] { lblMicrophoneDesc, lblMicrophone, cmbMicrophone });

            // ==============================
            // TAB: ТОКЕНИ
            // ==============================
            lblPicovoiceKey.Text = "Picovoice Access Key:";
            lblPicovoiceKey.Location = new Point(lx, 18);
            lblPicovoiceKey.AutoSize = true;
            lblPicovoiceKey.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);

            txtPicovoiceKey.Location = new Point(lx, 38);
            txtPicovoiceKey.Size = new Size(530, 26);

            lblPicovoiceKeyHint.Text = "Ключ для Picovoice — розпізнавання слова-тригера (\"Alexa\", \"Jarvis\" тощо). Отримати на picovoice.ai.";
            lblPicovoiceKeyHint.Location = new Point(lx, 68);
            lblPicovoiceKeyHint.Size = new Size(530, 32);
            lblPicovoiceKeyHint.ForeColor = hintColor;

            lblOpenAiKey.Text = "OpenAI API Key:";
            lblOpenAiKey.Location = new Point(lx, 115);
            lblOpenAiKey.AutoSize = true;
            lblOpenAiKey.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);

            txtOpenAiKey.Location = new Point(lx, 135);
            txtOpenAiKey.Size = new Size(530, 26);

            lblOpenAiKeyHint.Text = "Ключ для ШІ-асистента (ChatGPT). Якщо порожньо або ШІ вимкнений — ChatGPT не використовується.\nОтримати на platform.openai.com.";
            lblOpenAiKeyHint.Location = new Point(lx, 165);
            lblOpenAiKeyHint.Size = new Size(530, 34);
            lblOpenAiKeyHint.ForeColor = hintColor;

            tabTokens.Controls.AddRange(new Control[] {
                lblPicovoiceKey, txtPicovoiceKey, lblPicovoiceKeyHint,
                lblOpenAiKey, txtOpenAiKey, lblOpenAiKeyHint
            });

            // ==============================
            // TAB: СЛОВО-ТРИГЕР
            // ==============================
            rbStandardWakeWord.Text = "Вбудоване слово-тригер";
            rbStandardWakeWord.Location = new Point(lx, 18);
            rbStandardWakeWord.Size = new Size(230, 22);
            rbStandardWakeWord.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);
            rbStandardWakeWord.CheckedChanged += rbStandardWakeWord_CheckedChanged;

            lblWakeWordStandardLabel.Text = "Слово:";
            lblWakeWordStandardLabel.Location = new Point(lx + 20, 46);
            lblWakeWordStandardLabel.AutoSize = true;

            cmbWakeWordStandard.Location = new Point(lx + 70, 43);
            cmbWakeWordStandard.Size = new Size(200, 26);
            cmbWakeWordStandard.DropDownStyle = ComboBoxStyle.DropDownList;
            cmbWakeWordStandard.Items.AddRange(new object[] {
                "alexa", "porcupine", "jarvis", "bumblebee",
                "hey google", "hey siri", "ok google",
                "computer", "terminator", "americano",
                "blueberry", "grapefruit"
            });

            rbCustomWakeWord.Text = "Власне слово-тригер (.ppn файл)";
            rbCustomWakeWord.Location = new Point(lx, 82);
            rbCustomWakeWord.Size = new Size(300, 22);
            rbCustomWakeWord.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);
            rbCustomWakeWord.CheckedChanged += rbCustomWakeWord_CheckedChanged;

            lblCustomWakeWordPath.Text = "Шлях до .ppn:";
            lblCustomWakeWordPath.Location = new Point(lx + 20, 110);
            lblCustomWakeWordPath.AutoSize = true;

            txtCustomWakeWordPath.Location = new Point(lx + 20, 130);
            txtCustomWakeWordPath.Size = new Size(400, 26);

            btnBrowsePpn.Text = "Огляд...";
            btnBrowsePpn.Location = new Point(lx + 430, 130);
            btnBrowsePpn.Size = new Size(80, 26);
            btnBrowsePpn.Click += btnBrowsePpn_Click;

            lblCustomWakeWordHint.Text = "Власну .ppn модель можна створити на console.picovoice.ai для будь-якого слова і мови.";
            lblCustomWakeWordHint.Location = new Point(lx + 20, 160);
            lblCustomWakeWordHint.Size = new Size(510, 20);
            lblCustomWakeWordHint.ForeColor = hintColor;

            lblSensitivity.Text = "Чутливість розпізнавання слова-тригера:";
            lblSensitivity.Location = new Point(lx, 195);
            lblSensitivity.AutoSize = true;
            lblSensitivity.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);

            trackSensitivity.Location = new Point(lx, 218);
            trackSensitivity.Size = new Size(450, 35);
            trackSensitivity.Minimum = 0;
            trackSensitivity.Maximum = 100;
            trackSensitivity.TickFrequency = 10;
            trackSensitivity.Scroll += trackSensitivity_Scroll;

            lblSensitivityValue.Text = "0.50";
            lblSensitivityValue.Location = new Point(lx + 462, 228);
            lblSensitivityValue.AutoSize = true;
            lblSensitivityValue.Font = new Font("Segoe UI", 10f, FontStyle.Bold);

            lblSensitivityHint.Text = "Менше (0.0) → рідше хибні спрацювання.  Більше (1.0) → краще чує, але більше помилок.";
            lblSensitivityHint.Location = new Point(lx, 258);
            lblSensitivityHint.Size = new Size(530, 20);
            lblSensitivityHint.ForeColor = hintColor;

            tabWakeWord.Controls.AddRange(new Control[] {
                rbStandardWakeWord, lblWakeWordStandardLabel, cmbWakeWordStandard,
                rbCustomWakeWord, lblCustomWakeWordPath, txtCustomWakeWordPath, btnBrowsePpn,
                lblCustomWakeWordHint,
                lblSensitivity, trackSensitivity, lblSensitivityValue, lblSensitivityHint
            });

            // ==============================
            // TAB: ГОЛОС / ШІ
            // ==============================
            chkTtsEnabled.Text = "Озвучувати відповіді (Text-to-Speech)";
            chkTtsEnabled.Location = new Point(lx, 18);
            chkTtsEnabled.AutoSize = true;
            chkTtsEnabled.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);

            lblTtsHint.Text = "Асистент вимовлятиме відповіді вголос. Якщо вимкнено — лише звукові сигнали (listen.wav / end.wav).";
            lblTtsHint.Location = new Point(lx + 20, 42);
            lblTtsHint.Size = new Size(520, 20);
            lblTtsHint.ForeColor = hintColor;

            lblTtsVoice.Text = "Голос для озвучення:";
            lblTtsVoice.Location = new Point(lx, 75);
            lblTtsVoice.AutoSize = true;
            lblTtsVoice.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);

            cmbTtsVoice.Location = new Point(lx, 95);
            cmbTtsVoice.Size = new Size(370, 26);
            cmbTtsVoice.DropDownStyle = ComboBoxStyle.DropDownList;
            // Заповнюється в InitVoiceCombo()

            lblTtsVoiceHint.Text = "Голос Microsoft Edge TTS. Українські голоси: Остап (чоловічий), Поліна (жіночий).";
            lblTtsVoiceHint.Location = new Point(lx, 125);
            lblTtsVoiceHint.Size = new Size(520, 20);
            lblTtsVoiceHint.ForeColor = hintColor;

            lblTtsRate.Text = "Швидкість мовлення:";
            lblTtsRate.Location = new Point(lx, 158);
            lblTtsRate.AutoSize = true;
            lblTtsRate.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);

            txtTtsRate.Location = new Point(lx, 178);
            txtTtsRate.Size = new Size(120, 26);

            lblTtsRateHint.Text = "Наприклад: +25% (швидше), -10% (повільніше), 0% (нормально).";
            lblTtsRateHint.Location = new Point(lx, 208);
            lblTtsRateHint.Size = new Size(520, 20);
            lblTtsRateHint.ForeColor = hintColor;

            lblLanguagesTitle.Text = "Мови розпізнавання (активні одночасно):";
            lblLanguagesTitle.Location = new Point(lx, 242);
            lblLanguagesTitle.AutoSize = true;
            lblLanguagesTitle.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);

            lblLanguagesHint.Text = "Асистент пробує розпізнати мовлення на всіх обраних мовах одночасно і бере найкращий результат.";
            lblLanguagesHint.Location = new Point(lx, 264);
            lblLanguagesHint.Size = new Size(520, 20);
            lblLanguagesHint.ForeColor = hintColor;

            pnlLanguages.Location = new Point(lx, 288);
            pnlLanguages.Size = new Size(530, 80);
            pnlLanguages.FlowDirection = FlowDirection.LeftToRight;
            pnlLanguages.WrapContents = true;
            pnlLanguages.AutoSize = false;
            pnlLanguages.BackColor = Color.Transparent;

            tabModel.Controls.AddRange(new Control[] {
                chkTtsEnabled, lblTtsHint,
                lblTtsVoice, cmbTtsVoice, lblTtsVoiceHint,
                lblTtsRate, txtTtsRate, lblTtsRateHint,
                lblLanguagesTitle, lblLanguagesHint, pnlLanguages
            });

            // ==============================
            // TAB: СЛУХАННЯ
            // ==============================
            int row(int n) => 18 + n * 82;

            lblCommandTimeout.Text = "Час очікування команди (секунди):";
            lblCommandTimeout.Location = new Point(lx, row(0));
            lblCommandTimeout.AutoSize = true;
            lblCommandTimeout.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);

            nudCommandTimeout.Location = new Point(440, row(0) - 2);
            nudCommandTimeout.Size = new Size(80, 26);
            nudCommandTimeout.Minimum = 1;
            nudCommandTimeout.Maximum = 120;

            lblCommandTimeoutHint.Text = "Скільки секунд чекати на команду після спрацювання слова-тригера.\nЯкщо нічого не сказано — сесія закривається автоматично.";
            lblCommandTimeoutHint.Location = new Point(lx, row(0) + 22);
            lblCommandTimeoutHint.Size = new Size(420, 34);
            lblCommandTimeoutHint.ForeColor = hintColor;

            lblContinuousListen.Text = "Продовження сесії після команди (секунди):";
            lblContinuousListen.Location = new Point(lx, row(1));
            lblContinuousListen.AutoSize = true;
            lblContinuousListen.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);

            nudContinuousListen.Location = new Point(440, row(1) - 2);
            nudContinuousListen.Size = new Size(80, 26);
            nudContinuousListen.Minimum = 1;
            nudContinuousListen.Maximum = 60;

            lblContinuousListenHint.Text = "Після виконання команди сесія продовжується на цей час — можна сказати ще одну команду.";
            lblContinuousListenHint.Location = new Point(lx, row(1) + 22);
            lblContinuousListenHint.Size = new Size(420, 20);
            lblContinuousListenHint.ForeColor = hintColor;

            lblSilenceDetect.Text = "Тиша для зупинки запису (секунди):";
            lblSilenceDetect.Location = new Point(lx, row(2));
            lblSilenceDetect.AutoSize = true;
            lblSilenceDetect.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);

            nudSilenceDetect.Location = new Point(440, row(2) - 2);
            nudSilenceDetect.Size = new Size(80, 26);
            nudSilenceDetect.Minimum = 0;
            nudSilenceDetect.Maximum = 30;
            nudSilenceDetect.DecimalPlaces = 1;
            nudSilenceDetect.Increment = 0.5m;

            lblSilenceDetectHint.Text = "Якщо мікрофон мовчить довше цього часу — запис команди зупиняється і відправляється на розпізнавання.";
            lblSilenceDetectHint.Location = new Point(lx, row(2) + 22);
            lblSilenceDetectHint.Size = new Size(420, 20);
            lblSilenceDetectHint.ForeColor = hintColor;

            lblSilenceTimeout.Text = "Загальний таймаут тиші (секунди):";
            lblSilenceTimeout.Location = new Point(lx, row(3));
            lblSilenceTimeout.AutoSize = true;
            lblSilenceTimeout.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);

            nudSilenceTimeout.Location = new Point(440, row(3) - 2);
            nudSilenceTimeout.Size = new Size(80, 26);
            nudSilenceTimeout.Minimum = 0;
            nudSilenceTimeout.Maximum = 60;
            nudSilenceTimeout.DecimalPlaces = 1;
            nudSilenceTimeout.Increment = 0.5m;

            lblSilenceTimeoutHint.Text = "Максимальний час тиші в сесії загалом до її примусового завершення.";
            lblSilenceTimeoutHint.Location = new Point(lx, row(3) + 22);
            lblSilenceTimeoutHint.Size = new Size(420, 20);
            lblSilenceTimeoutHint.ForeColor = hintColor;

            tabListening.Controls.AddRange(new Control[] {
                lblCommandTimeout, nudCommandTimeout, lblCommandTimeoutHint,
                lblContinuousListen, nudContinuousListen, lblContinuousListenHint,
                lblSilenceDetect, nudSilenceDetect, lblSilenceDetectHint,
                lblSilenceTimeout, nudSilenceTimeout, lblSilenceTimeoutHint
            });

            // ==============================
            // TAB: СИСТЕМА
            // ==============================
            chkAutostart.Text = "Запускати асистента при старті Windows";
            chkAutostart.Location = new Point(lx, 18);
            chkAutostart.AutoSize = true;
            chkAutostart.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);
            chkAutostart.CheckedChanged += chkAutostart_CheckedChanged;

            lblAutostartHint.Text = "Додає Alexa.exe до автозапуску через реєстр Windows\n(HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run).\nНе потребує прав адміністратора.";
            lblAutostartHint.Location = new Point(lx + 20, 45);
            lblAutostartHint.Size = new Size(520, 52);
            lblAutostartHint.ForeColor = hintColor;

            lblAutostartPath.Text = "Шлях до exe: не знайдено";
            lblAutostartPath.Location = new Point(lx, 112);
            lblAutostartPath.Size = new Size(530, 18);
            lblAutostartPath.ForeColor = Color.FromArgb(130, 130, 140);
            lblAutostartPath.Font = new Font("Segoe UI", 8.5f);

            tabSystem.Controls.AddRange(new Control[] {
                chkAutostart, lblAutostartHint, lblAutostartPath
            });

            // ==============================
            // BOTTOM BUTTONS
            // ==============================
            lblConfigPath.Text = "";
            lblConfigPath.Location = new Point(12, 468);
            lblConfigPath.Size = new Size(400, 18);
            lblConfigPath.ForeColor = hintColor;
            lblConfigPath.Font = new Font("Segoe UI", 8f);

            btnReload.Text = "Перезавантажити";
            btnReload.Location = new Point(415, 463);
            btnReload.Size = new Size(85, 32);
            btnReload.Click += btnReload_Click;

            btnSave.Text = "Зберегти";
            btnSave.Location = new Point(507, 463);
            btnSave.Size = new Size(85, 32);
            btnSave.Font = new Font("Segoe UI", 9.5f, FontStyle.Bold);
            btnSave.BackColor = Color.FromArgb(37, 99, 235);
            btnSave.ForeColor = Color.White;
            btnSave.FlatStyle = FlatStyle.Flat;
            btnSave.Click += btnSave_Click;

            Controls.AddRange(new Control[] { tabControl, btnSave, btnReload, lblConfigPath });

            tabControl.ResumeLayout(false);
            ((System.ComponentModel.ISupportInitialize)trackSensitivity).EndInit();
            ((System.ComponentModel.ISupportInitialize)nudCommandTimeout).EndInit();
            ((System.ComponentModel.ISupportInitialize)nudContinuousListen).EndInit();
            ((System.ComponentModel.ISupportInitialize)nudSilenceDetect).EndInit();
            ((System.ComponentModel.ISupportInitialize)nudSilenceTimeout).EndInit();
            ResumeLayout(false);
        }

        #endregion

        // Controls
        private TabControl tabControl;
        private TabPage tabMicrophone, tabTokens, tabWakeWord, tabModel, tabListening;

        private Label lblMicrophoneDesc, lblMicrophone;
        private ComboBox cmbMicrophone;

        private Label lblPicovoiceKey, lblPicovoiceKeyHint, lblOpenAiKey, lblOpenAiKeyHint;
        private TextBox txtPicovoiceKey, txtOpenAiKey;

        private RadioButton rbStandardWakeWord, rbCustomWakeWord;
        private Label lblWakeWordStandardLabel, lblCustomWakeWordPath, lblCustomWakeWordHint;
        private Label lblSensitivity, lblSensitivityValue, lblSensitivityHint;
        private ComboBox cmbWakeWordStandard;
        private TextBox txtCustomWakeWordPath;
        private Button btnBrowsePpn;
        private TrackBar trackSensitivity;

        private Label lblTtsHint, lblTtsVoice, lblTtsVoiceHint;
        private Label lblTtsRate, lblTtsRateHint;
        private Label lblLanguagesTitle, lblLanguagesHint;
        private CheckBox chkTtsEnabled;
        private ComboBox cmbTtsVoice;
        private TextBox txtTtsRate;
        private FlowLayoutPanel pnlLanguages;

        private Label lblCommandTimeout, lblCommandTimeoutHint;
        private Label lblContinuousListen, lblContinuousListenHint;
        private Label lblSilenceDetect, lblSilenceDetectHint;
        private Label lblSilenceTimeout, lblSilenceTimeoutHint;
        private NumericUpDown nudCommandTimeout, nudContinuousListen, nudSilenceDetect, nudSilenceTimeout;

        private Button btnSave, btnReload;
        private Label lblConfigPath;

        private TabPage tabSystem;
        private CheckBox chkAutostart;
        private Label lblAutostartHint, lblAutostartPath;
    }
}
