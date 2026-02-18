namespace AlexaS
{
    partial class Form1
    {
        private System.ComponentModel.IContainer components = null;

        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        private void InitializeComponent()
        {
            this.lblTitle = new System.Windows.Forms.Label();
            this.lblSubtitle = new System.Windows.Forms.Label();
            this.panelDivider = new System.Windows.Forms.Panel();

            this.groupBoxKeys = new System.Windows.Forms.GroupBox();
            this.lblPicovoiceKey = new System.Windows.Forms.Label();
            this.txtPicovoiceKey = new System.Windows.Forms.TextBox();
            this.lblOpenAIKey = new System.Windows.Forms.Label();
            this.txtOpenAIKey = new System.Windows.Forms.TextBox();

            this.groupBoxWakeWord = new System.Windows.Forms.GroupBox();
            this.rbStandardWakeWord = new System.Windows.Forms.RadioButton();
            this.rbCustomWakeWord = new System.Windows.Forms.RadioButton();
            this.cmbWakeWordStandard = new System.Windows.Forms.ComboBox();
            this.txtCustomWakeWordPath = new System.Windows.Forms.TextBox();
            this.btnBrowseWakeWord = new System.Windows.Forms.Button();

            this.groupBoxTiming = new System.Windows.Forms.GroupBox();
            this.lblSensitivity = new System.Windows.Forms.Label();
            this.trackSensitivity = new System.Windows.Forms.TrackBar();
            this.lblSensitivityValue = new System.Windows.Forms.Label();
            this.lblCommandTimeout = new System.Windows.Forms.Label();
            this.numCommandTimeout = new System.Windows.Forms.NumericUpDown();
            this.lblSeconds1 = new System.Windows.Forms.Label();
            this.lblListenSeconds = new System.Windows.Forms.Label();
            this.numListenSeconds = new System.Windows.Forms.NumericUpDown();
            this.lblSeconds2 = new System.Windows.Forms.Label();
            this.lblSilenceDetect = new System.Windows.Forms.Label();
            this.numSilenceDetect = new System.Windows.Forms.NumericUpDown();
            this.lblSeconds3 = new System.Windows.Forms.Label();
            this.lblSilenceTimeout = new System.Windows.Forms.Label();
            this.numSilenceTimeout = new System.Windows.Forms.NumericUpDown();
            this.lblSeconds4 = new System.Windows.Forms.Label();

            this.groupBoxTTS = new System.Windows.Forms.GroupBox();
            this.chkTtsEnabled = new System.Windows.Forms.CheckBox();
            this.lblVoiceGender = new System.Windows.Forms.Label();
            this.rbMaleVoice = new System.Windows.Forms.RadioButton();
            this.rbFemaleVoice = new System.Windows.Forms.RadioButton();
            this.lblVoiceSpeed = new System.Windows.Forms.Label();
            this.trackVoiceSpeed = new System.Windows.Forms.TrackBar();
            this.lblVoiceSpeedValue = new System.Windows.Forms.Label();
            this.btnTestVoice = new System.Windows.Forms.Button();

            this.panelFooter = new System.Windows.Forms.Panel();
            this.btnSaveAndClose = new System.Windows.Forms.Button();
            this.btnSaveAndRestart = new System.Windows.Forms.Button();
            this.btnLaunchAlexa = new System.Windows.Forms.Button();

            this.groupBoxKeys.SuspendLayout();
            this.groupBoxWakeWord.SuspendLayout();
            this.groupBoxTiming.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.trackSensitivity)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.numCommandTimeout)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.numListenSeconds)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.numSilenceDetect)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.numSilenceTimeout)).BeginInit();
            this.groupBoxTTS.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.trackVoiceSpeed)).BeginInit();
            this.panelFooter.SuspendLayout();
            this.SuspendLayout();

            // ── Accent & background colors ──────────────────────────────────
            var accent = System.Drawing.Color.FromArgb(0, 174, 219);
            var accentDark = System.Drawing.Color.FromArgb(0, 122, 180);
            var bgDark = System.Drawing.Color.FromArgb(18, 18, 24);
            var bgCard = System.Drawing.Color.FromArgb(30, 32, 42);
            var bgInput = System.Drawing.Color.FromArgb(40, 43, 56);
            var borderColor = System.Drawing.Color.FromArgb(55, 60, 78);
            var textPrimary = System.Drawing.Color.FromArgb(230, 232, 240);
            var textMuted = System.Drawing.Color.FromArgb(140, 148, 170);
            var green = System.Drawing.Color.FromArgb(34, 197, 94);
            var orange = System.Drawing.Color.FromArgb(251, 146, 60);

            int formW = 620;
            int padX = 24;
            int cardW = formW - padX * 2;  // 572

            // ── Header ──────────────────────────────────────────────────────
            // lblTitle
            this.lblTitle.AutoSize = false;
            this.lblTitle.Font = new System.Drawing.Font("Segoe UI", 18F, System.Drawing.FontStyle.Bold);
            this.lblTitle.ForeColor = accent;
            this.lblTitle.Location = new System.Drawing.Point(padX, 22);
            this.lblTitle.Size = new System.Drawing.Size(cardW, 36);
            this.lblTitle.Name = "lblTitle";
            this.lblTitle.TabIndex = 0;
            this.lblTitle.Text = "Голосовий асистент";

            // lblSubtitle
            this.lblSubtitle.AutoSize = false;
            this.lblSubtitle.Font = new System.Drawing.Font("Segoe UI", 9F);
            this.lblSubtitle.ForeColor = textMuted;
            this.lblSubtitle.Location = new System.Drawing.Point(padX, 60);
            this.lblSubtitle.Size = new System.Drawing.Size(cardW, 20);
            this.lblSubtitle.Name = "lblSubtitle";
            this.lblSubtitle.TabIndex = 1;
            this.lblSubtitle.Text = "Налаштування та конфігурація";

            // panelDivider
            this.panelDivider.BackColor = borderColor;
            this.panelDivider.Location = new System.Drawing.Point(padX, 86);
            this.panelDivider.Size = new System.Drawing.Size(cardW, 1);
            this.panelDivider.Name = "panelDivider";
            this.panelDivider.TabIndex = 2;

            // ── Helper: style GroupBox ───────────────────────────────────────
            System.Action<System.Windows.Forms.GroupBox, int> styleGroup = (gb, y) => {
                gb.BackColor = bgCard;
                gb.ForeColor = accent;
                gb.Font = new System.Drawing.Font("Segoe UI Semibold", 9.5F, System.Drawing.FontStyle.Bold);
                gb.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
                gb.Location = new System.Drawing.Point(padX, y);
                gb.Size = new System.Drawing.Size(cardW, 0); // height set below
                gb.Padding = new System.Windows.Forms.Padding(14, 6, 14, 12);
                gb.TabStop = false;
            };

            // ── Helper: style Label ─────────────────────────────────────────
            System.Action<System.Windows.Forms.Label, string, int, int> styleLabel = (l, text, x, y) => {
                l.AutoSize = true;
                l.Font = new System.Drawing.Font("Segoe UI", 9F);
                l.ForeColor = textPrimary;
                l.Location = new System.Drawing.Point(x, y);
                l.Text = text;
            };

            // ── Helper: style TextBox ───────────────────────────────────────
            System.Action<System.Windows.Forms.TextBox, int, int, int> styleTxt = (t, x, y, w) => {
                t.BackColor = bgInput;
                t.ForeColor = textPrimary;
                t.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
                t.Font = new System.Drawing.Font("Segoe UI", 9.5F);
                t.Location = new System.Drawing.Point(x, y);
                t.Size = new System.Drawing.Size(w, 26);
            };

            // ── Helper: style NumericUpDown ─────────────────────────────────
            System.Action<System.Windows.Forms.NumericUpDown, int, int> styleNum = (n, x, y) => {
                n.BackColor = bgInput;
                n.ForeColor = textPrimary;
                n.Font = new System.Drawing.Font("Segoe UI", 9.5F);
                n.Location = new System.Drawing.Point(x, y);
                n.Size = new System.Drawing.Size(75, 26);
            };

            // ── Helper: style RadioButton ───────────────────────────────────
            System.Action<System.Windows.Forms.RadioButton, int, int> styleRb = (rb, x, y) => {
                rb.AutoSize = true;
                rb.Font = new System.Drawing.Font("Segoe UI", 9.5F);
                rb.ForeColor = textPrimary;
                rb.Location = new System.Drawing.Point(x, y);
                rb.UseVisualStyleBackColor = false;
                rb.BackColor = System.Drawing.Color.Transparent;
            };

            // ═══════════════════════════════════════════════════════
            // GROUP 1 — API Keys   (top y = 102)
            // ═══════════════════════════════════════════════════════
            int g1y = 102;
            styleGroup(this.groupBoxKeys, g1y);
            this.groupBoxKeys.Size = new System.Drawing.Size(cardW, 130);
            this.groupBoxKeys.Text = "  🔑  API Ключі";
            this.groupBoxKeys.Name = "groupBoxKeys";
            this.groupBoxKeys.TabIndex = 3;
            this.groupBoxKeys.Controls.Add(this.lblPicovoiceKey);
            this.groupBoxKeys.Controls.Add(this.txtPicovoiceKey);
            this.groupBoxKeys.Controls.Add(this.lblOpenAIKey);
            this.groupBoxKeys.Controls.Add(this.txtOpenAIKey);

            styleLabel(this.lblPicovoiceKey, "Picovoice Access Key", 14, 28);
            this.lblPicovoiceKey.Name = "lblPicovoiceKey"; this.lblPicovoiceKey.TabIndex = 0;

            styleTxt(this.txtPicovoiceKey, 14, 48, cardW - 28);
            this.txtPicovoiceKey.Name = "txtPicovoiceKey";
            this.txtPicovoiceKey.PasswordChar = '●';
            this.txtPicovoiceKey.TabIndex = 1;
            this.txtPicovoiceKey.TextChanged += new System.EventHandler(this.txtPicovoiceKey_TextChanged);

            styleLabel(this.lblOpenAIKey, "OpenAI API Key", 14, 84);
            this.lblOpenAIKey.Name = "lblOpenAIKey"; this.lblOpenAIKey.TabIndex = 2;

            styleTxt(this.txtOpenAIKey, 14, 104, cardW - 28);
            this.txtOpenAIKey.Name = "txtOpenAIKey";
            this.txtOpenAIKey.PasswordChar = '●';
            this.txtOpenAIKey.TabIndex = 3;
            this.txtOpenAIKey.TextChanged += new System.EventHandler(this.txtOpenAIKey_TextChanged);

            // ═══════════════════════════════════════════════════════
            // GROUP 2 — Wake Word   (y = g1y + 130 + 12 = 244)
            // ═══════════════════════════════════════════════════════
            int g2y = g1y + 130 + 12;
            styleGroup(this.groupBoxWakeWord, g2y);
            this.groupBoxWakeWord.Size = new System.Drawing.Size(cardW, 122);
            this.groupBoxWakeWord.Text = "  🎙  Wake Word (слово активації)";
            this.groupBoxWakeWord.Name = "groupBoxWakeWord";
            this.groupBoxWakeWord.TabIndex = 4;
            this.groupBoxWakeWord.Controls.Add(this.rbStandardWakeWord);
            this.groupBoxWakeWord.Controls.Add(this.cmbWakeWordStandard);
            this.groupBoxWakeWord.Controls.Add(this.rbCustomWakeWord);
            this.groupBoxWakeWord.Controls.Add(this.txtCustomWakeWordPath);
            this.groupBoxWakeWord.Controls.Add(this.btnBrowseWakeWord);

            // Row 1 — Standard
            styleRb(this.rbStandardWakeWord, 14, 30);
            this.rbStandardWakeWord.Text = "Стандартне:";
            this.rbStandardWakeWord.Checked = true;
            this.rbStandardWakeWord.TabStop = true;
            this.rbStandardWakeWord.Name = "rbStandardWakeWord";
            this.rbStandardWakeWord.TabIndex = 0;
            this.rbStandardWakeWord.CheckedChanged += new System.EventHandler(this.rbStandardWakeWord_CheckedChanged);

            this.cmbWakeWordStandard.BackColor = bgInput;
            this.cmbWakeWordStandard.ForeColor = textPrimary;
            this.cmbWakeWordStandard.Font = new System.Drawing.Font("Segoe UI", 9.5F);
            this.cmbWakeWordStandard.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbWakeWordStandard.FormattingEnabled = true;
            this.cmbWakeWordStandard.Items.AddRange(new object[] { "alexa", "jarvis" });
            this.cmbWakeWordStandard.Location = new System.Drawing.Point(140, 27);
            this.cmbWakeWordStandard.Size = new System.Drawing.Size(140, 26);
            this.cmbWakeWordStandard.Name = "cmbWakeWordStandard";
            this.cmbWakeWordStandard.TabIndex = 1;
            this.cmbWakeWordStandard.SelectedIndexChanged += new System.EventHandler(this.cmbWakeWordStandard_SelectedIndexChanged);

            // Row 2 — Custom
            styleRb(this.rbCustomWakeWord, 14, 72);
            this.rbCustomWakeWord.Text = "Своє:";
            this.rbCustomWakeWord.Name = "rbCustomWakeWord";
            this.rbCustomWakeWord.TabIndex = 2;
            this.rbCustomWakeWord.CheckedChanged += new System.EventHandler(this.rbCustomWakeWord_CheckedChanged);

            styleTxt(this.txtCustomWakeWordPath, 90, 70, cardW - 28 - 90 - 70);
            this.txtCustomWakeWordPath.Enabled = false;
            this.txtCustomWakeWordPath.ReadOnly = true;
            this.txtCustomWakeWordPath.Name = "txtCustomWakeWordPath";
            this.txtCustomWakeWordPath.TabIndex = 3;

            this.btnBrowseWakeWord.BackColor = accentDark;
            this.btnBrowseWakeWord.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnBrowseWakeWord.FlatAppearance.BorderSize = 0;
            this.btnBrowseWakeWord.ForeColor = System.Drawing.Color.White;
            this.btnBrowseWakeWord.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Bold);
            this.btnBrowseWakeWord.Enabled = false;
            this.btnBrowseWakeWord.Location = new System.Drawing.Point(cardW - 28 - 66, 68);
            this.btnBrowseWakeWord.Size = new System.Drawing.Size(66, 28);
            this.btnBrowseWakeWord.Name = "btnBrowseWakeWord";
            this.btnBrowseWakeWord.TabIndex = 4;
            this.btnBrowseWakeWord.Text = "Обрати";
            this.btnBrowseWakeWord.UseVisualStyleBackColor = false;
            this.btnBrowseWakeWord.Click += new System.EventHandler(this.btnBrowseWakeWord_Click);

            // ═══════════════════════════════════════════════════════
            // GROUP 3 — Timing   (y = g2y + 122 + 12)
            // ═══════════════════════════════════════════════════════
            int g3y = g2y + 122 + 12;
            styleGroup(this.groupBoxTiming, g3y);
            this.groupBoxTiming.Size = new System.Drawing.Size(cardW, 212);
            this.groupBoxTiming.Text = "  ⏱  Чутливість та тайм-аути";
            this.groupBoxTiming.Name = "groupBoxTiming";
            this.groupBoxTiming.TabIndex = 5;
            this.groupBoxTiming.Controls.Add(this.lblSensitivity);
            this.groupBoxTiming.Controls.Add(this.trackSensitivity);
            this.groupBoxTiming.Controls.Add(this.lblSensitivityValue);
            this.groupBoxTiming.Controls.Add(this.lblCommandTimeout);
            this.groupBoxTiming.Controls.Add(this.numCommandTimeout);
            this.groupBoxTiming.Controls.Add(this.lblSeconds1);
            this.groupBoxTiming.Controls.Add(this.lblListenSeconds);
            this.groupBoxTiming.Controls.Add(this.numListenSeconds);
            this.groupBoxTiming.Controls.Add(this.lblSeconds2);
            this.groupBoxTiming.Controls.Add(this.lblSilenceDetect);
            this.groupBoxTiming.Controls.Add(this.numSilenceDetect);
            this.groupBoxTiming.Controls.Add(this.lblSeconds3);
            this.groupBoxTiming.Controls.Add(this.lblSilenceTimeout);
            this.groupBoxTiming.Controls.Add(this.numSilenceTimeout);
            this.groupBoxTiming.Controls.Add(this.lblSeconds4);

            // Row 1 — Sensitivity slider  (full width)
            styleLabel(this.lblSensitivity, "Чутливість:", 14, 30);
            this.lblSensitivity.Name = "lblSensitivity"; this.lblSensitivity.TabIndex = 0;

            this.trackSensitivity.BackColor = bgCard;
            this.trackSensitivity.Location = new System.Drawing.Point(120, 24);
            this.trackSensitivity.Size = new System.Drawing.Size(cardW - 120 - 60, 42);
            this.trackSensitivity.Maximum = 100; this.trackSensitivity.Minimum = 0;
            this.trackSensitivity.TickFrequency = 10; this.trackSensitivity.Value = 50;
            this.trackSensitivity.Name = "trackSensitivity"; this.trackSensitivity.TabIndex = 1;
            this.trackSensitivity.Scroll += new System.EventHandler(this.trackSensitivity_Scroll);

            this.lblSensitivityValue.AutoSize = false;
            this.lblSensitivityValue.Font = new System.Drawing.Font("Segoe UI Semibold", 9.5F, System.Drawing.FontStyle.Bold);
            this.lblSensitivityValue.ForeColor = accent;
            this.lblSensitivityValue.Location = new System.Drawing.Point(cardW - 56, 30);
            this.lblSensitivityValue.Size = new System.Drawing.Size(42, 20);
            this.lblSensitivityValue.TextAlign = System.Drawing.ContentAlignment.MiddleRight;
            this.lblSensitivityValue.Name = "lblSensitivityValue"; this.lblSensitivityValue.TabIndex = 2;
            this.lblSensitivityValue.Text = "50%";

            // Rows 2-5 — numeric grid  (2 columns)
            int col1x = 14; int col2x = (cardW / 2) + 6;
            int rowBase = 78; int rowH = 40;

            // Col 1, Row 1 — Command timeout
            styleLabel(this.lblCommandTimeout, "Тайм-аут команди:", col1x, rowBase + 4);
            this.lblCommandTimeout.Name = "lblCommandTimeout"; this.lblCommandTimeout.TabIndex = 3;
            styleNum(this.numCommandTimeout, col1x + 160, rowBase);
            this.numCommandTimeout.Minimum = 1; this.numCommandTimeout.Maximum = 60; this.numCommandTimeout.Value = 15;
            this.numCommandTimeout.Name = "numCommandTimeout"; this.numCommandTimeout.TabIndex = 4;
            this.numCommandTimeout.ValueChanged += new System.EventHandler(this.numCommandTimeout_ValueChanged);
            styleLabel(this.lblSeconds1, "сек", col1x + 160 + 78, rowBase + 4);
            this.lblSeconds1.ForeColor = textMuted; this.lblSeconds1.Name = "lblSeconds1"; this.lblSeconds1.TabIndex = 5;

            // Col 2, Row 1 — Listen seconds
            styleLabel(this.lblListenSeconds, "Слухати команду:", col2x, rowBase + 4);
            this.lblListenSeconds.Name = "lblListenSeconds"; this.lblListenSeconds.TabIndex = 6;
            styleNum(this.numListenSeconds, col2x + 148, rowBase);
            this.numListenSeconds.Minimum = 1; this.numListenSeconds.Maximum = 30; this.numListenSeconds.Value = 7;
            this.numListenSeconds.Name = "numListenSeconds"; this.numListenSeconds.TabIndex = 7;
            this.numListenSeconds.ValueChanged += new System.EventHandler(this.numListenSeconds_ValueChanged);
            styleLabel(this.lblSeconds2, "сек", col2x + 148 + 78, rowBase + 4);
            this.lblSeconds2.ForeColor = textMuted; this.lblSeconds2.Name = "lblSeconds2"; this.lblSeconds2.TabIndex = 8;

            // Col 1, Row 2 — Silence detect
            styleLabel(this.lblSilenceDetect, "Виявлення тиші:", col1x, rowBase + rowH + 4);
            this.lblSilenceDetect.Name = "lblSilenceDetect"; this.lblSilenceDetect.TabIndex = 9;
            styleNum(this.numSilenceDetect, col1x + 160, rowBase + rowH);
            this.numSilenceDetect.DecimalPlaces = 1;
            this.numSilenceDetect.Increment = new decimal(new int[] { 1, 0, 0, 65536 });
            this.numSilenceDetect.Minimum = new decimal(new int[] { 1, 0, 0, 65536 });
            this.numSilenceDetect.Maximum = new decimal(new int[] { 10, 0, 0, 0 });
            this.numSilenceDetect.Value = new decimal(new int[] { 15, 0, 0, 65536 });
            this.numSilenceDetect.Name = "numSilenceDetect"; this.numSilenceDetect.TabIndex = 10;
            this.numSilenceDetect.ValueChanged += new System.EventHandler(this.numSilenceDetect_ValueChanged);
            styleLabel(this.lblSeconds3, "сек", col1x + 160 + 78, rowBase + rowH + 4);
            this.lblSeconds3.ForeColor = textMuted; this.lblSeconds3.Name = "lblSeconds3"; this.lblSeconds3.TabIndex = 11;

            // Col 2, Row 2 — Silence timeout
            styleLabel(this.lblSilenceTimeout, "Тайм-аут тиші:", col2x, rowBase + rowH + 4);
            this.lblSilenceTimeout.Name = "lblSilenceTimeout"; this.lblSilenceTimeout.TabIndex = 12;
            styleNum(this.numSilenceTimeout, col2x + 148, rowBase + rowH);
            this.numSilenceTimeout.DecimalPlaces = 1;
            this.numSilenceTimeout.Increment = new decimal(new int[] { 1, 0, 0, 65536 });
            this.numSilenceTimeout.Minimum = new decimal(new int[] { 1, 0, 0, 0 });
            this.numSilenceTimeout.Maximum = new decimal(new int[] { 60, 0, 0, 0 });
            this.numSilenceTimeout.Value = new decimal(new int[] { 5, 0, 0, 0 });
            this.numSilenceTimeout.Name = "numSilenceTimeout"; this.numSilenceTimeout.TabIndex = 13;
            this.numSilenceTimeout.ValueChanged += new System.EventHandler(this.numSilenceTimeout_ValueChanged);
            styleLabel(this.lblSeconds4, "сек", col2x + 148 + 78, rowBase + rowH + 4);
            this.lblSeconds4.ForeColor = textMuted; this.lblSeconds4.Name = "lblSeconds4"; this.lblSeconds4.TabIndex = 14;

            // ═══════════════════════════════════════════════════════
            // GROUP 4 — TTS   (y = g3y + 212 + 12)
            // ═══════════════════════════════════════════════════════
            int g4y = g3y + 212 + 12;
            styleGroup(this.groupBoxTTS, g4y);
            this.groupBoxTTS.Size = new System.Drawing.Size(cardW, 155);
            this.groupBoxTTS.Text = "  🔊  Голосові відповіді (TTS)";
            this.groupBoxTTS.Name = "groupBoxTTS";
            this.groupBoxTTS.TabIndex = 6;
            this.groupBoxTTS.Controls.Add(this.chkTtsEnabled);
            this.groupBoxTTS.Controls.Add(this.lblVoiceGender);
            this.groupBoxTTS.Controls.Add(this.rbMaleVoice);
            this.groupBoxTTS.Controls.Add(this.rbFemaleVoice);
            this.groupBoxTTS.Controls.Add(this.lblVoiceSpeed);
            this.groupBoxTTS.Controls.Add(this.trackVoiceSpeed);
            this.groupBoxTTS.Controls.Add(this.lblVoiceSpeedValue);
            this.groupBoxTTS.Controls.Add(this.btnTestVoice);

            // Row 1 — CheckBox
            this.chkTtsEnabled.AutoSize = true;
            this.chkTtsEnabled.Checked = true;
            this.chkTtsEnabled.CheckState = System.Windows.Forms.CheckState.Checked;
            this.chkTtsEnabled.Font = new System.Drawing.Font("Segoe UI", 9.5F);
            this.chkTtsEnabled.ForeColor = textPrimary;
            this.chkTtsEnabled.Location = new System.Drawing.Point(14, 28);
            this.chkTtsEnabled.UseVisualStyleBackColor = false;
            this.chkTtsEnabled.BackColor = System.Drawing.Color.Transparent;
            this.chkTtsEnabled.Text = "Увімкнути голосові відповіді";
            this.chkTtsEnabled.Name = "chkTtsEnabled"; this.chkTtsEnabled.TabIndex = 0;
            this.chkTtsEnabled.CheckedChanged += new System.EventHandler(this.chkTtsEnabled_CheckedChanged);

            // Row 2 — Voice gender
            styleLabel(this.lblVoiceGender, "Тип голосу:", 14, 64);
            this.lblVoiceGender.Name = "lblVoiceGender"; this.lblVoiceGender.TabIndex = 1;

            styleRb(this.rbMaleVoice, 120, 62);
            this.rbMaleVoice.Text = "Чоловічий (Jarvis)";
            this.rbMaleVoice.Checked = true;
            this.rbMaleVoice.TabStop = true;
            this.rbMaleVoice.Name = "rbMaleVoice"; this.rbMaleVoice.TabIndex = 2;
            this.rbMaleVoice.CheckedChanged += new System.EventHandler(this.rbMaleVoice_CheckedChanged);

            styleRb(this.rbFemaleVoice, 290, 62);
            this.rbFemaleVoice.Text = "Жіночий (Polina)";
            this.rbFemaleVoice.Name = "rbFemaleVoice"; this.rbFemaleVoice.TabIndex = 3;
            this.rbFemaleVoice.CheckedChanged += new System.EventHandler(this.rbFemaleVoice_CheckedChanged);

            // Row 3 — Speed slider + test button
            styleLabel(this.lblVoiceSpeed, "Швидкість:", 14, 104);
            this.lblVoiceSpeed.Name = "lblVoiceSpeed"; this.lblVoiceSpeed.TabIndex = 4;

            this.trackVoiceSpeed.BackColor = bgCard;
            this.trackVoiceSpeed.Location = new System.Drawing.Point(112, 98);
            this.trackVoiceSpeed.Size = new System.Drawing.Size(220, 42);
            this.trackVoiceSpeed.Minimum = -50; this.trackVoiceSpeed.Maximum = 100;
            this.trackVoiceSpeed.TickFrequency = 10; this.trackVoiceSpeed.Value = 30;
            this.trackVoiceSpeed.Name = "trackVoiceSpeed"; this.trackVoiceSpeed.TabIndex = 5;
            this.trackVoiceSpeed.Scroll += new System.EventHandler(this.trackVoiceSpeed_Scroll);

            this.lblVoiceSpeedValue.AutoSize = false;
            this.lblVoiceSpeedValue.Font = new System.Drawing.Font("Segoe UI Semibold", 9.5F, System.Drawing.FontStyle.Bold);
            this.lblVoiceSpeedValue.ForeColor = accent;
            this.lblVoiceSpeedValue.Location = new System.Drawing.Point(336, 104);
            this.lblVoiceSpeedValue.Size = new System.Drawing.Size(48, 20);
            this.lblVoiceSpeedValue.TextAlign = System.Drawing.ContentAlignment.MiddleLeft;
            this.lblVoiceSpeedValue.Name = "lblVoiceSpeedValue"; this.lblVoiceSpeedValue.TabIndex = 6;
            this.lblVoiceSpeedValue.Text = "+30%";

            this.btnTestVoice.BackColor = green;
            this.btnTestVoice.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnTestVoice.FlatAppearance.BorderSize = 0;
            this.btnTestVoice.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Bold);
            this.btnTestVoice.ForeColor = System.Drawing.Color.White;
            this.btnTestVoice.Location = new System.Drawing.Point(cardW - 28 - 120, 100);
            this.btnTestVoice.Size = new System.Drawing.Size(120, 30);
            this.btnTestVoice.Name = "btnTestVoice"; this.btnTestVoice.TabIndex = 7;
            this.btnTestVoice.Text = "▶  Прослухати";
            this.btnTestVoice.UseVisualStyleBackColor = false;
            this.btnTestVoice.Click += new System.EventHandler(this.btnTestVoice_Click);

            // ═══════════════════════════════════════════════════════
            // FOOTER PANEL
            // ═══════════════════════════════════════════════════════
            int footerY = g4y + 155 + 16;
            this.panelFooter.BackColor = System.Drawing.Color.FromArgb(24, 26, 35);
            this.panelFooter.Location = new System.Drawing.Point(0, footerY);
            this.panelFooter.Size = new System.Drawing.Size(formW, 60);
            this.panelFooter.Name = "panelFooter"; this.panelFooter.TabIndex = 7;
            this.panelFooter.Controls.Add(this.btnSaveAndClose);
            this.panelFooter.Controls.Add(this.btnSaveAndRestart);
            this.panelFooter.Controls.Add(this.btnLaunchAlexa);

            int bH = 38; int bY = (60 - bH) / 2;

            // btnSaveAndClose
            this.btnSaveAndClose.BackColor = accentDark;
            this.btnSaveAndClose.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnSaveAndClose.FlatAppearance.BorderSize = 0;
            this.btnSaveAndClose.Font = new System.Drawing.Font("Segoe UI", 9.5F, System.Drawing.FontStyle.Bold);
            this.btnSaveAndClose.ForeColor = System.Drawing.Color.White;
            this.btnSaveAndClose.Location = new System.Drawing.Point(padX, bY);
            this.btnSaveAndClose.Size = new System.Drawing.Size(130, bH);
            this.btnSaveAndClose.Name = "btnSaveAndClose"; this.btnSaveAndClose.TabIndex = 0;
            this.btnSaveAndClose.Text = "💾  Зберегти";
            this.btnSaveAndClose.UseVisualStyleBackColor = false;
            this.btnSaveAndClose.Click += new System.EventHandler(this.btnSaveAndClose_Click);

            // btnSaveAndRestart
            this.btnSaveAndRestart.BackColor = orange;
            this.btnSaveAndRestart.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnSaveAndRestart.FlatAppearance.BorderSize = 0;
            this.btnSaveAndRestart.Font = new System.Drawing.Font("Segoe UI", 9.5F, System.Drawing.FontStyle.Bold);
            this.btnSaveAndRestart.ForeColor = System.Drawing.Color.White;
            this.btnSaveAndRestart.Location = new System.Drawing.Point(padX + 130 + 10, bY);
            this.btnSaveAndRestart.Size = new System.Drawing.Size(196, bH);
            this.btnSaveAndRestart.Name = "btnSaveAndRestart"; this.btnSaveAndRestart.TabIndex = 1;
            this.btnSaveAndRestart.Text = "🔄  Зберегти та перезапустити";
            this.btnSaveAndRestart.UseVisualStyleBackColor = false;
            this.btnSaveAndRestart.Click += new System.EventHandler(this.btnSaveAndRestart_Click);

            // btnLaunchAlexa
            this.btnLaunchAlexa.BackColor = green;
            this.btnLaunchAlexa.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnLaunchAlexa.FlatAppearance.BorderSize = 0;
            this.btnLaunchAlexa.Font = new System.Drawing.Font("Segoe UI", 9.5F, System.Drawing.FontStyle.Bold);
            this.btnLaunchAlexa.ForeColor = System.Drawing.Color.White;
            this.btnLaunchAlexa.Location = new System.Drawing.Point(formW - padX - 170, bY);
            this.btnLaunchAlexa.Size = new System.Drawing.Size(170, bH);
            this.btnLaunchAlexa.Name = "btnLaunchAlexa"; this.btnLaunchAlexa.TabIndex = 2;
            this.btnLaunchAlexa.Text = "▶  Запустити асистента";
            this.btnLaunchAlexa.UseVisualStyleBackColor = false;
            this.btnLaunchAlexa.Click += new System.EventHandler(this.btnLaunchAlexa_Click);

            // ═══════════════════════════════════════════════════════
            // FORM itself
            // ═══════════════════════════════════════════════════════
            int formH = footerY + 60;

            this.AutoScaleDimensions = new System.Drawing.SizeF(8F, 19F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.BackColor = bgDark;
            this.ClientSize = new System.Drawing.Size(formW, formH);
            this.Font = new System.Drawing.Font("Segoe UI", 10F);
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedSingle;
            this.MaximizeBox = false;
            this.Name = "Form1";
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
            this.Text = "Налаштування Голосового Асистента";

            this.Controls.Add(this.lblTitle);
            this.Controls.Add(this.lblSubtitle);
            this.Controls.Add(this.panelDivider);
            this.Controls.Add(this.groupBoxKeys);
            this.Controls.Add(this.groupBoxWakeWord);
            this.Controls.Add(this.groupBoxTiming);
            this.Controls.Add(this.groupBoxTTS);
            this.Controls.Add(this.panelFooter);

            this.groupBoxKeys.ResumeLayout(false);
            this.groupBoxKeys.PerformLayout();
            this.groupBoxWakeWord.ResumeLayout(false);
            this.groupBoxWakeWord.PerformLayout();
            this.groupBoxTiming.ResumeLayout(false);
            this.groupBoxTiming.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.trackSensitivity)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.numCommandTimeout)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.numListenSeconds)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.numSilenceDetect)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.numSilenceTimeout)).EndInit();
            this.groupBoxTTS.ResumeLayout(false);
            this.groupBoxTTS.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.trackVoiceSpeed)).EndInit();
            this.panelFooter.ResumeLayout(false);
            this.ResumeLayout(false);
            this.PerformLayout();
        }

        #endregion

        private System.Windows.Forms.Label lblTitle;
        private System.Windows.Forms.Label lblSubtitle;
        private System.Windows.Forms.Panel panelDivider;
        private System.Windows.Forms.GroupBox groupBoxKeys;
        private System.Windows.Forms.Label lblPicovoiceKey;
        private System.Windows.Forms.TextBox txtPicovoiceKey;
        private System.Windows.Forms.Label lblOpenAIKey;
        private System.Windows.Forms.TextBox txtOpenAIKey;
        private System.Windows.Forms.GroupBox groupBoxWakeWord;
        private System.Windows.Forms.RadioButton rbStandardWakeWord;
        private System.Windows.Forms.RadioButton rbCustomWakeWord;
        private System.Windows.Forms.ComboBox cmbWakeWordStandard;
        private System.Windows.Forms.TextBox txtCustomWakeWordPath;
        private System.Windows.Forms.Button btnBrowseWakeWord;
        private System.Windows.Forms.GroupBox groupBoxTiming;
        private System.Windows.Forms.Label lblSensitivity;
        private System.Windows.Forms.TrackBar trackSensitivity;
        private System.Windows.Forms.Label lblSensitivityValue;
        private System.Windows.Forms.Label lblCommandTimeout;
        private System.Windows.Forms.NumericUpDown numCommandTimeout;
        private System.Windows.Forms.Label lblSeconds1;
        private System.Windows.Forms.Label lblListenSeconds;
        private System.Windows.Forms.NumericUpDown numListenSeconds;
        private System.Windows.Forms.Label lblSeconds2;
        private System.Windows.Forms.Label lblSilenceDetect;
        private System.Windows.Forms.NumericUpDown numSilenceDetect;
        private System.Windows.Forms.Label lblSeconds3;
        private System.Windows.Forms.Label lblSilenceTimeout;
        private System.Windows.Forms.NumericUpDown numSilenceTimeout;
        private System.Windows.Forms.Label lblSeconds4;
        private System.Windows.Forms.GroupBox groupBoxTTS;
        private System.Windows.Forms.CheckBox chkTtsEnabled;
        private System.Windows.Forms.Label lblVoiceGender;
        private System.Windows.Forms.RadioButton rbMaleVoice;
        private System.Windows.Forms.RadioButton rbFemaleVoice;
        private System.Windows.Forms.Label lblVoiceSpeed;
        private System.Windows.Forms.TrackBar trackVoiceSpeed;
        private System.Windows.Forms.Label lblVoiceSpeedValue;
        private System.Windows.Forms.Button btnTestVoice;
        private System.Windows.Forms.Panel panelFooter;
        private System.Windows.Forms.Button btnSaveAndClose;
        private System.Windows.Forms.Button btnSaveAndRestart;
        private System.Windows.Forms.Button btnLaunchAlexa;
    }
}