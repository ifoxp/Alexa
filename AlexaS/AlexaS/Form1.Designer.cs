using System.Drawing;
using System.Drawing.Drawing2D;
using System.Windows.Forms;

namespace AlexaS
{
    partial class Form1
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.panelHeader = new System.Windows.Forms.Panel();
            this.lblSubtitle = new System.Windows.Forms.Label();
            this.lblTitle = new System.Windows.Forms.Label();
            this.panelMain = new System.Windows.Forms.Panel();
            this.panelRight = new System.Windows.Forms.Panel();
            this.panelTiming = new System.Windows.Forms.Panel();
            this.numSilenceDetectSeconds = new System.Windows.Forms.NumericUpDown();
            this.numContinuousListenSeconds = new System.Windows.Forms.NumericUpDown();
            this.numCommandSessionTimeout = new System.Windows.Forms.NumericUpDown();
            this.lblSilenceDetectSeconds = new System.Windows.Forms.Label();
            this.lblContinuousListenSeconds = new System.Windows.Forms.Label();
            this.lblCommandSessionTimeout = new System.Windows.Forms.Label();
            this.lblTimingTitle = new System.Windows.Forms.Label();
            this.panelSettings = new System.Windows.Forms.Panel();
            this.trackSensitivity = new System.Windows.Forms.TrackBar();
            this.lblSensitivityValue = new System.Windows.Forms.Label();
            this.lblSensitivity = new System.Windows.Forms.Label();
            this.cmbLanguage = new System.Windows.Forms.ComboBox();
            this.lblLanguage = new System.Windows.Forms.Label();
            this.lblSettingsTitle = new System.Windows.Forms.Label();
            this.panelLeft = new System.Windows.Forms.Panel();
            this.panelWakeWord = new System.Windows.Forms.Panel();
            this.btnBrowseCustomWakeWord = new System.Windows.Forms.Button();
            this.txtCustomWakeWordPath = new System.Windows.Forms.TextBox();
            this.lblCustomWakeWordPath = new System.Windows.Forms.Label();
            this.cmbWakeWord = new System.Windows.Forms.ComboBox();
            this.radioCustom = new System.Windows.Forms.RadioButton();
            this.radioStandard = new System.Windows.Forms.RadioButton();
            this.lblWakeWordTitle = new System.Windows.Forms.Label();
            this.panelAPI = new System.Windows.Forms.Panel();
            this.btnPicovoiceHelp = new System.Windows.Forms.Button();
            this.btnPicovoiceWebsite = new System.Windows.Forms.Button();
            this.txtPicovoiceKey = new System.Windows.Forms.TextBox();
            this.lblPicovoiceKey = new System.Windows.Forms.Label();
            this.lblAPITitle = new System.Windows.Forms.Label();
            this.panelJarvis = new System.Windows.Forms.Panel();
            this.btnSelectJarvis = new System.Windows.Forms.Button();
            this.lblJarvisPath = new System.Windows.Forms.Label();
            this.lblJarvisLabel = new System.Windows.Forms.Label();
            this.lblJarvisTitle = new System.Windows.Forms.Label();
            this.panelFooter = new System.Windows.Forms.Panel();
            this.btnManageCommands = new System.Windows.Forms.Button();
            this.btnSaveAndRestart = new System.Windows.Forms.Button();
            this.btnSave = new System.Windows.Forms.Button();
            this.panelHeader.SuspendLayout();
            this.panelMain.SuspendLayout();
            this.panelRight.SuspendLayout();
            this.panelTiming.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.numSilenceDetectSeconds)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.numContinuousListenSeconds)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.numCommandSessionTimeout)).BeginInit();
            this.panelSettings.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.trackSensitivity)).BeginInit();
            this.panelLeft.SuspendLayout();
            this.panelWakeWord.SuspendLayout();
            this.panelAPI.SuspendLayout();
            this.panelJarvis.SuspendLayout();
            this.panelFooter.SuspendLayout();
            this.SuspendLayout();
            // 
            // panelHeader
            // 
            this.panelHeader.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(45)))), ((int)(((byte)(50)))), ((int)(((byte)(55)))));
            this.panelHeader.Controls.Add(this.lblSubtitle);
            this.panelHeader.Controls.Add(this.lblTitle);
            this.panelHeader.Dock = System.Windows.Forms.DockStyle.Top;
            this.panelHeader.Location = new System.Drawing.Point(0, 0);
            this.panelHeader.Name = "panelHeader";
            this.panelHeader.Padding = new System.Windows.Forms.Padding(30, 15, 30, 15);
            this.panelHeader.Size = new System.Drawing.Size(1200, 70);
            this.panelHeader.TabIndex = 0;
            this.panelHeader.Paint += new System.Windows.Forms.PaintEventHandler(this.panelHeader_Paint);
            // 
            // lblSubtitle
            // 
            this.lblSubtitle.AutoSize = true;
            this.lblSubtitle.BackColor = System.Drawing.Color.Transparent;
            this.lblSubtitle.Font = new System.Drawing.Font("Segoe UI", 8.5F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.lblSubtitle.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(220)))), ((int)(((byte)(220)))), ((int)(((byte)(220)))));
            this.lblSubtitle.Location = new System.Drawing.Point(32, 42);
            this.lblSubtitle.Name = "lblSubtitle";
            this.lblSubtitle.Size = new System.Drawing.Size(273, 15);
            this.lblSubtitle.TabIndex = 1;
            this.lblSubtitle.Text = "Професійна конфігурація голосового асистента";
            // 
            // lblTitle
            // 
            this.lblTitle.AutoSize = true;
            this.lblTitle.BackColor = System.Drawing.Color.Transparent;
            this.lblTitle.Font = new System.Drawing.Font("Segoe UI", 16F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.lblTitle.ForeColor = System.Drawing.Color.White;
            this.lblTitle.Location = new System.Drawing.Point(28, 15);
            this.lblTitle.Name = "lblTitle";
            this.lblTitle.Size = new System.Drawing.Size(225, 30);
            this.lblTitle.TabIndex = 0;
            this.lblTitle.Text = "⚡ ALEXA SETTINGS";
            // 
            // panelMain
            // 
            this.panelMain.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(35)))), ((int)(((byte)(40)))), ((int)(((byte)(45)))));
            this.panelMain.Controls.Add(this.panelRight);
            this.panelMain.Controls.Add(this.panelLeft);
            this.panelMain.Dock = System.Windows.Forms.DockStyle.Fill;
            this.panelMain.Location = new System.Drawing.Point(0, 70);
            this.panelMain.Name = "panelMain";
            this.panelMain.Padding = new System.Windows.Forms.Padding(20, 15, 20, 15);
            this.panelMain.Size = new System.Drawing.Size(1200, 450);
            this.panelMain.TabIndex = 1;
            // 
            // panelRight
            // 
            this.panelRight.Controls.Add(this.panelTiming);
            this.panelRight.Controls.Add(this.panelSettings);
            this.panelRight.Dock = System.Windows.Forms.DockStyle.Fill;
            this.panelRight.Location = new System.Drawing.Point(605, 15);
            this.panelRight.Name = "panelRight";
            this.panelRight.Padding = new System.Windows.Forms.Padding(10, 0, 0, 0);
            this.panelRight.Size = new System.Drawing.Size(575, 420);
            this.panelRight.TabIndex = 1;
            // 
            // panelTiming
            // 
            this.panelTiming.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(45)))), ((int)(((byte)(50)))), ((int)(((byte)(55)))));
            this.panelTiming.Controls.Add(this.numSilenceDetectSeconds);
            this.panelTiming.Controls.Add(this.numContinuousListenSeconds);
            this.panelTiming.Controls.Add(this.numCommandSessionTimeout);
            this.panelTiming.Controls.Add(this.lblSilenceDetectSeconds);
            this.panelTiming.Controls.Add(this.lblContinuousListenSeconds);
            this.panelTiming.Controls.Add(this.lblCommandSessionTimeout);
            this.panelTiming.Controls.Add(this.lblTimingTitle);
            this.panelTiming.Dock = System.Windows.Forms.DockStyle.Top;
            this.panelTiming.Location = new System.Drawing.Point(10, 195);
            this.panelTiming.Name = "panelTiming";
            this.panelTiming.Size = new System.Drawing.Size(565, 195);
            this.panelTiming.TabIndex = 1;
            // 
            // numSilenceDetectSeconds
            // 
            this.numSilenceDetectSeconds.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(60)))), ((int)(((byte)(65)))), ((int)(((byte)(70)))));
            this.numSilenceDetectSeconds.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.numSilenceDetectSeconds.DecimalPlaces = 1;
            this.numSilenceDetectSeconds.Font = new System.Drawing.Font("Segoe UI", 9.75F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.numSilenceDetectSeconds.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(242)))), ((int)(((byte)(242)))), ((int)(((byte)(247)))));
            this.numSilenceDetectSeconds.Increment = new decimal(new int[] {
            1,
            0,
            0,
            65536});
            this.numSilenceDetectSeconds.Location = new System.Drawing.Point(240, 145);
            this.numSilenceDetectSeconds.Maximum = new decimal(new int[] {
            5,
            0,
            0,
            0});
            this.numSilenceDetectSeconds.Minimum = new decimal(new int[] {
            5,
            0,
            0,
            65536});
            this.numSilenceDetectSeconds.Name = "numSilenceDetectSeconds";
            this.numSilenceDetectSeconds.Size = new System.Drawing.Size(90, 25);
            this.numSilenceDetectSeconds.TabIndex = 6;
            this.numSilenceDetectSeconds.Value = new decimal(new int[] {
            15,
            0,
            0,
            65536});
            // 
            // numContinuousListenSeconds
            // 
            this.numContinuousListenSeconds.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(60)))), ((int)(((byte)(65)))), ((int)(((byte)(70)))));
            this.numContinuousListenSeconds.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.numContinuousListenSeconds.Font = new System.Drawing.Font("Segoe UI", 9.75F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.numContinuousListenSeconds.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(242)))), ((int)(((byte)(242)))), ((int)(((byte)(247)))));
            this.numContinuousListenSeconds.Location = new System.Drawing.Point(240, 100);
            this.numContinuousListenSeconds.Maximum = new decimal(new int[] {
            30,
            0,
            0,
            0});
            this.numContinuousListenSeconds.Minimum = new decimal(new int[] {
            1,
            0,
            0,
            0});
            this.numContinuousListenSeconds.Name = "numContinuousListenSeconds";
            this.numContinuousListenSeconds.Size = new System.Drawing.Size(90, 25);
            this.numContinuousListenSeconds.TabIndex = 5;
            this.numContinuousListenSeconds.Value = new decimal(new int[] {
            7,
            0,
            0,
            0});
            // 
            // numCommandSessionTimeout
            // 
            this.numCommandSessionTimeout.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(60)))), ((int)(((byte)(65)))), ((int)(((byte)(70)))));
            this.numCommandSessionTimeout.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.numCommandSessionTimeout.Font = new System.Drawing.Font("Segoe UI", 9.75F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.numCommandSessionTimeout.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(242)))), ((int)(((byte)(242)))), ((int)(((byte)(247)))));
            this.numCommandSessionTimeout.Location = new System.Drawing.Point(240, 55);
            this.numCommandSessionTimeout.Maximum = new decimal(new int[] {
            60,
            0,
            0,
            0});
            this.numCommandSessionTimeout.Minimum = new decimal(new int[] {
            5,
            0,
            0,
            0});
            this.numCommandSessionTimeout.Name = "numCommandSessionTimeout";
            this.numCommandSessionTimeout.Size = new System.Drawing.Size(90, 25);
            this.numCommandSessionTimeout.TabIndex = 4;
            this.numCommandSessionTimeout.Value = new decimal(new int[] {
            15,
            0,
            0,
            0});
            // 
            // lblSilenceDetectSeconds
            // 
            this.lblSilenceDetectSeconds.AutoSize = true;
            this.lblSilenceDetectSeconds.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.lblSilenceDetectSeconds.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(142)))), ((int)(((byte)(142)))), ((int)(((byte)(147)))));
            this.lblSilenceDetectSeconds.Location = new System.Drawing.Point(20, 147);
            this.lblSilenceDetectSeconds.Name = "lblSilenceDetectSeconds";
            this.lblSilenceDetectSeconds.Size = new System.Drawing.Size(128, 15);
            this.lblSilenceDetectSeconds.TabIndex = 3;
            this.lblSilenceDetectSeconds.Text = "Тривалість тиші (сек):";
            // 
            // lblContinuousListenSeconds
            // 
            this.lblContinuousListenSeconds.AutoSize = true;
            this.lblContinuousListenSeconds.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.lblContinuousListenSeconds.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(142)))), ((int)(((byte)(142)))), ((int)(((byte)(147)))));
            this.lblContinuousListenSeconds.Location = new System.Drawing.Point(20, 102);
            this.lblContinuousListenSeconds.Name = "lblContinuousListenSeconds";
            this.lblContinuousListenSeconds.Size = new System.Drawing.Size(160, 15);
            this.lblContinuousListenSeconds.TabIndex = 2;
            this.lblContinuousListenSeconds.Text = "Додаткове очікування (сек):";
            // 
            // lblCommandSessionTimeout
            // 
            this.lblCommandSessionTimeout.AutoSize = true;
            this.lblCommandSessionTimeout.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.lblCommandSessionTimeout.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(142)))), ((int)(((byte)(142)))), ((int)(((byte)(147)))));
            this.lblCommandSessionTimeout.Location = new System.Drawing.Point(20, 57);
            this.lblCommandSessionTimeout.Name = "lblCommandSessionTimeout";
            this.lblCommandSessionTimeout.Size = new System.Drawing.Size(174, 15);
            this.lblCommandSessionTimeout.TabIndex = 1;
            this.lblCommandSessionTimeout.Text = "Час очікування команди (сек):";
            // 
            // lblTimingTitle
            // 
            this.lblTimingTitle.AutoSize = true;
            this.lblTimingTitle.Font = new System.Drawing.Font("Segoe UI Semibold", 10F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.lblTimingTitle.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(242)))), ((int)(((byte)(242)))), ((int)(((byte)(247)))));
            this.lblTimingTitle.Location = new System.Drawing.Point(15, 12);
            this.lblTimingTitle.Name = "lblTimingTitle";
            this.lblTimingTitle.Size = new System.Drawing.Size(161, 19);
            this.lblTimingTitle.TabIndex = 0;
            this.lblTimingTitle.Text = "⏱️ Налаштування часу";
            // 
            // panelSettings
            // 
            this.panelSettings.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(45)))), ((int)(((byte)(50)))), ((int)(((byte)(55)))));
            this.panelSettings.Controls.Add(this.trackSensitivity);
            this.panelSettings.Controls.Add(this.lblSensitivityValue);
            this.panelSettings.Controls.Add(this.lblSensitivity);
            this.panelSettings.Controls.Add(this.cmbLanguage);
            this.panelSettings.Controls.Add(this.lblLanguage);
            this.panelSettings.Controls.Add(this.lblSettingsTitle);
            this.panelSettings.Dock = System.Windows.Forms.DockStyle.Top;
            this.panelSettings.Location = new System.Drawing.Point(10, 0);
            this.panelSettings.Name = "panelSettings";
            this.panelSettings.Size = new System.Drawing.Size(565, 195);
            this.panelSettings.TabIndex = 0;
            // 
            // trackSensitivity
            // 
            this.trackSensitivity.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(45)))), ((int)(((byte)(50)))), ((int)(((byte)(55)))));
            this.trackSensitivity.Location = new System.Drawing.Point(20, 125);
            this.trackSensitivity.Margin = new System.Windows.Forms.Padding(20, 3, 20, 3);
            this.trackSensitivity.Maximum = 100;
            this.trackSensitivity.Name = "trackSensitivity";
            this.trackSensitivity.Size = new System.Drawing.Size(520, 45);
            this.trackSensitivity.TabIndex = 5;
            this.trackSensitivity.TickFrequency = 10;
            this.trackSensitivity.Value = 50;
            this.trackSensitivity.ValueChanged += new System.EventHandler(this.trackSensitivity_ValueChanged);
            // 
            // lblSensitivityValue
            // 
            this.lblSensitivityValue.AutoSize = true;
            this.lblSensitivityValue.Font = new System.Drawing.Font("Segoe UI Semibold", 10F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.lblSensitivityValue.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(95)))), ((int)(((byte)(135)))), ((int)(((byte)(165)))));
            this.lblSensitivityValue.Location = new System.Drawing.Point(110, 95);
            this.lblSensitivityValue.Name = "lblSensitivityValue";
            this.lblSensitivityValue.Size = new System.Drawing.Size(36, 19);
            this.lblSensitivityValue.TabIndex = 4;
            this.lblSensitivityValue.Text = "0.50";
            // 
            // lblSensitivity
            // 
            this.lblSensitivity.AutoSize = true;
            this.lblSensitivity.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.lblSensitivity.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(142)))), ((int)(((byte)(142)))), ((int)(((byte)(147)))));
            this.lblSensitivity.Location = new System.Drawing.Point(20, 97);
            this.lblSensitivity.Name = "lblSensitivity";
            this.lblSensitivity.Size = new System.Drawing.Size(69, 15);
            this.lblSensitivity.TabIndex = 3;
            this.lblSensitivity.Text = "Чутливість:";
            // 
            // cmbLanguage
            // 
            this.cmbLanguage.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(60)))), ((int)(((byte)(65)))), ((int)(((byte)(70)))));
            this.cmbLanguage.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbLanguage.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.cmbLanguage.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.cmbLanguage.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(242)))), ((int)(((byte)(242)))), ((int)(((byte)(247)))));
            this.cmbLanguage.FormattingEnabled = true;
            this.cmbLanguage.Items.AddRange(new object[] {
            "🇺🇦 Українська (uk-UA)",
            "🇺🇸 Англійська (en-US)",
            "🇵🇱 Польська (pl-PL)",
            "🇩🇪 Німецька (de-DE)",
            "🇷🇺 Російська (ru-RU)"});
            this.cmbLanguage.Location = new System.Drawing.Point(180, 55);
            this.cmbLanguage.Name = "cmbLanguage";
            this.cmbLanguage.Size = new System.Drawing.Size(220, 23);
            this.cmbLanguage.TabIndex = 2;
            // 
            // lblLanguage
            // 
            this.lblLanguage.AutoSize = true;
            this.lblLanguage.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.lblLanguage.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(142)))), ((int)(((byte)(142)))), ((int)(((byte)(147)))));
            this.lblLanguage.Location = new System.Drawing.Point(20, 57);
            this.lblLanguage.Name = "lblLanguage";
            this.lblLanguage.Size = new System.Drawing.Size(122, 15);
            this.lblLanguage.TabIndex = 1;
            this.lblLanguage.Text = "Мова розпізнавання:";
            // 
            // lblSettingsTitle
            // 
            this.lblSettingsTitle.AutoSize = true;
            this.lblSettingsTitle.Font = new System.Drawing.Font("Segoe UI Semibold", 10F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.lblSettingsTitle.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(242)))), ((int)(((byte)(242)))), ((int)(((byte)(247)))));
            this.lblSettingsTitle.Location = new System.Drawing.Point(15, 12);
            this.lblSettingsTitle.Name = "lblSettingsTitle";
            this.lblSettingsTitle.Size = new System.Drawing.Size(184, 19);
            this.lblSettingsTitle.TabIndex = 0;
            this.lblSettingsTitle.Text = "⚙️ Основні налаштування";
            // 
            // panelLeft
            // 
            this.panelLeft.Controls.Add(this.panelWakeWord);
            this.panelLeft.Controls.Add(this.panelAPI);
            this.panelLeft.Controls.Add(this.panelJarvis);
            this.panelLeft.Dock = System.Windows.Forms.DockStyle.Left;
            this.panelLeft.Location = new System.Drawing.Point(20, 15);
            this.panelLeft.Name = "panelLeft";
            this.panelLeft.Padding = new System.Windows.Forms.Padding(0, 0, 10, 0);
            this.panelLeft.Size = new System.Drawing.Size(585, 420);
            this.panelLeft.TabIndex = 0;
            // 
            // panelWakeWord
            // 
            this.panelWakeWord.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(45)))), ((int)(((byte)(50)))), ((int)(((byte)(55)))));
            this.panelWakeWord.Controls.Add(this.btnBrowseCustomWakeWord);
            this.panelWakeWord.Controls.Add(this.txtCustomWakeWordPath);
            this.panelWakeWord.Controls.Add(this.lblCustomWakeWordPath);
            this.panelWakeWord.Controls.Add(this.cmbWakeWord);
            this.panelWakeWord.Controls.Add(this.radioCustom);
            this.panelWakeWord.Controls.Add(this.radioStandard);
            this.panelWakeWord.Controls.Add(this.lblWakeWordTitle);
            this.panelWakeWord.Dock = System.Windows.Forms.DockStyle.Top;
            this.panelWakeWord.Location = new System.Drawing.Point(0, 220);
            this.panelWakeWord.Name = "panelWakeWord";
            this.panelWakeWord.Size = new System.Drawing.Size(575, 170);
            this.panelWakeWord.TabIndex = 2;
            this.panelWakeWord.Paint += new System.Windows.Forms.PaintEventHandler(this.panelCard_Paint);
            // 
            // btnBrowseCustomWakeWord
            // 
            this.btnBrowseCustomWakeWord.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.btnBrowseCustomWakeWord.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(95)))), ((int)(((byte)(135)))), ((int)(((byte)(165)))));
            this.btnBrowseCustomWakeWord.Cursor = System.Windows.Forms.Cursors.Hand;
            this.btnBrowseCustomWakeWord.Enabled = false;
            this.btnBrowseCustomWakeWord.FlatAppearance.BorderSize = 0;
            this.btnBrowseCustomWakeWord.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnBrowseCustomWakeWord.Font = new System.Drawing.Font("Segoe UI Semibold", 9F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.btnBrowseCustomWakeWord.ForeColor = System.Drawing.Color.White;
            this.btnBrowseCustomWakeWord.Location = new System.Drawing.Point(470, 135);
            this.btnBrowseCustomWakeWord.Name = "btnBrowseCustomWakeWord";
            this.btnBrowseCustomWakeWord.Size = new System.Drawing.Size(85, 25);
            this.btnBrowseCustomWakeWord.TabIndex = 6;
            this.btnBrowseCustomWakeWord.Text = "Огляд...";
            this.btnBrowseCustomWakeWord.UseVisualStyleBackColor = false;
            this.btnBrowseCustomWakeWord.MouseEnter += new System.EventHandler(this.Button_MouseEnter);
            this.btnBrowseCustomWakeWord.MouseLeave += new System.EventHandler(this.Button_MouseLeave);
            // 
            // txtCustomWakeWordPath
            // 
            this.txtCustomWakeWordPath.Anchor = ((System.Windows.Forms.AnchorStyles)(((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Left) 
            | System.Windows.Forms.AnchorStyles.Right)));
            this.txtCustomWakeWordPath.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(60)))), ((int)(((byte)(65)))), ((int)(((byte)(70)))));
            this.txtCustomWakeWordPath.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.txtCustomWakeWordPath.Enabled = false;
            this.txtCustomWakeWordPath.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.txtCustomWakeWordPath.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(242)))), ((int)(((byte)(242)))), ((int)(((byte)(247)))));
            this.txtCustomWakeWordPath.Location = new System.Drawing.Point(20, 135);
            this.txtCustomWakeWordPath.Name = "txtCustomWakeWordPath";
            this.txtCustomWakeWordPath.Size = new System.Drawing.Size(440, 23);
            this.txtCustomWakeWordPath.TabIndex = 5;
            // 
            // lblCustomWakeWordPath
            // 
            this.lblCustomWakeWordPath.AutoSize = true;
            this.lblCustomWakeWordPath.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.lblCustomWakeWordPath.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(142)))), ((int)(((byte)(142)))), ((int)(((byte)(147)))));
            this.lblCustomWakeWordPath.Location = new System.Drawing.Point(20, 112);
            this.lblCustomWakeWordPath.Name = "lblCustomWakeWordPath";
            this.lblCustomWakeWordPath.Size = new System.Drawing.Size(132, 15);
            this.lblCustomWakeWordPath.TabIndex = 4;
            this.lblCustomWakeWordPath.Text = "Користувацький файл:";
            // 
            // cmbWakeWord
            // 
            this.cmbWakeWord.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(60)))), ((int)(((byte)(65)))), ((int)(((byte)(70)))));
            this.cmbWakeWord.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbWakeWord.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.cmbWakeWord.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.cmbWakeWord.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(242)))), ((int)(((byte)(242)))), ((int)(((byte)(247)))));
            this.cmbWakeWord.FormattingEnabled = true;
            this.cmbWakeWord.Items.AddRange(new object[] {
            "alexa",
            "jarvis",
            "computer",
            "hey google",
            "ok google",
            "hey siri",
            "picovoice",
            "porcupine",
            "bumblebee",
            "terminator"});
            this.cmbWakeWord.Location = new System.Drawing.Point(20, 75);
            this.cmbWakeWord.Name = "cmbWakeWord";
            this.cmbWakeWord.Size = new System.Drawing.Size(200, 23);
            this.cmbWakeWord.TabIndex = 3;
            // 
            // radioCustom
            // 
            this.radioCustom.AutoSize = true;
            this.radioCustom.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.radioCustom.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(242)))), ((int)(((byte)(242)))), ((int)(((byte)(247)))));
            this.radioCustom.Location = new System.Drawing.Point(180, 45);
            this.radioCustom.Name = "radioCustom";
            this.radioCustom.Size = new System.Drawing.Size(108, 19);
            this.radioCustom.TabIndex = 2;
            this.radioCustom.Text = "Власна модель";
            this.radioCustom.UseVisualStyleBackColor = true;
            this.radioCustom.CheckedChanged += new System.EventHandler(this.radioCustom_CheckedChanged);
            // 
            // radioStandard
            // 
            this.radioStandard.AutoSize = true;
            this.radioStandard.Checked = true;
            this.radioStandard.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.radioStandard.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(242)))), ((int)(((byte)(242)))), ((int)(((byte)(247)))));
            this.radioStandard.Location = new System.Drawing.Point(20, 45);
            this.radioStandard.Name = "radioStandard";
            this.radioStandard.Size = new System.Drawing.Size(124, 19);
            this.radioStandard.TabIndex = 1;
            this.radioStandard.TabStop = true;
            this.radioStandard.Text = "Стандартне слово";
            this.radioStandard.UseVisualStyleBackColor = true;
            // 
            // lblWakeWordTitle
            // 
            this.lblWakeWordTitle.AutoSize = true;
            this.lblWakeWordTitle.Font = new System.Drawing.Font("Segoe UI Semibold", 10F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.lblWakeWordTitle.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(242)))), ((int)(((byte)(242)))), ((int)(((byte)(247)))));
            this.lblWakeWordTitle.Location = new System.Drawing.Point(15, 12);
            this.lblWakeWordTitle.Name = "lblWakeWordTitle";
            this.lblWakeWordTitle.Size = new System.Drawing.Size(106, 19);
            this.lblWakeWordTitle.TabIndex = 0;
            this.lblWakeWordTitle.Text = "🎤 Wake Word";
            // 
            // panelAPI
            // 
            this.panelAPI.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(45)))), ((int)(((byte)(50)))), ((int)(((byte)(55)))));
            this.panelAPI.Controls.Add(this.btnPicovoiceHelp);
            this.panelAPI.Controls.Add(this.btnPicovoiceWebsite);
            this.panelAPI.Controls.Add(this.txtPicovoiceKey);
            this.panelAPI.Controls.Add(this.lblPicovoiceKey);
            this.panelAPI.Controls.Add(this.lblAPITitle);
            this.panelAPI.Dock = System.Windows.Forms.DockStyle.Top;
            this.panelAPI.Location = new System.Drawing.Point(0, 110);
            this.panelAPI.Name = "panelAPI";
            this.panelAPI.Size = new System.Drawing.Size(575, 110);
            this.panelAPI.TabIndex = 1;
            this.panelAPI.Paint += new System.Windows.Forms.PaintEventHandler(this.panelCard_Paint);
            // 
            // btnPicovoiceHelp
            // 
            this.btnPicovoiceHelp.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.btnPicovoiceHelp.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(95)))), ((int)(((byte)(135)))), ((int)(((byte)(165)))));
            this.btnPicovoiceHelp.Cursor = System.Windows.Forms.Cursors.Hand;
            this.btnPicovoiceHelp.FlatAppearance.BorderSize = 0;
            this.btnPicovoiceHelp.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnPicovoiceHelp.Font = new System.Drawing.Font("Segoe UI", 10F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.btnPicovoiceHelp.ForeColor = System.Drawing.Color.White;
            this.btnPicovoiceHelp.Location = new System.Drawing.Point(525, 68);
            this.btnPicovoiceHelp.Name = "btnPicovoiceHelp";
            this.btnPicovoiceHelp.Size = new System.Drawing.Size(30, 25);
            this.btnPicovoiceHelp.TabIndex = 4;
            this.btnPicovoiceHelp.Text = "?";
            this.btnPicovoiceHelp.UseVisualStyleBackColor = false;
            this.btnPicovoiceHelp.MouseEnter += new System.EventHandler(this.Button_MouseEnter);
            this.btnPicovoiceHelp.MouseLeave += new System.EventHandler(this.Button_MouseLeave);
            // 
            // btnPicovoiceWebsite
            // 
            this.btnPicovoiceWebsite.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Right)));
            this.btnPicovoiceWebsite.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(110)))), ((int)(((byte)(140)))), ((int)(((byte)(170)))));
            this.btnPicovoiceWebsite.Cursor = System.Windows.Forms.Cursors.Hand;
            this.btnPicovoiceWebsite.FlatAppearance.BorderSize = 0;
            this.btnPicovoiceWebsite.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnPicovoiceWebsite.Font = new System.Drawing.Font("Segoe UI Semibold", 9F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.btnPicovoiceWebsite.ForeColor = System.Drawing.Color.White;
            this.btnPicovoiceWebsite.Location = new System.Drawing.Point(395, 68);
            this.btnPicovoiceWebsite.Name = "btnPicovoiceWebsite";
            this.btnPicovoiceWebsite.Size = new System.Drawing.Size(120, 25);
            this.btnPicovoiceWebsite.TabIndex = 3;
            this.btnPicovoiceWebsite.Text = "Отримати ключ";
            this.btnPicovoiceWebsite.UseVisualStyleBackColor = false;
            this.btnPicovoiceWebsite.MouseEnter += new System.EventHandler(this.Button_MouseEnter);
            this.btnPicovoiceWebsite.MouseLeave += new System.EventHandler(this.Button_MouseLeave);
            // 
            // txtPicovoiceKey
            // 
            this.txtPicovoiceKey.Anchor = ((System.Windows.Forms.AnchorStyles)(((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Left) 
            | System.Windows.Forms.AnchorStyles.Right)));
            this.txtPicovoiceKey.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(60)))), ((int)(((byte)(65)))), ((int)(((byte)(70)))));
            this.txtPicovoiceKey.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.txtPicovoiceKey.Font = new System.Drawing.Font("Consolas", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.txtPicovoiceKey.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(242)))), ((int)(((byte)(242)))), ((int)(((byte)(247)))));
            this.txtPicovoiceKey.Location = new System.Drawing.Point(20, 68);
            this.txtPicovoiceKey.Name = "txtPicovoiceKey";
            this.txtPicovoiceKey.Size = new System.Drawing.Size(365, 22);
            this.txtPicovoiceKey.TabIndex = 2;
            // 
            // lblPicovoiceKey
            // 
            this.lblPicovoiceKey.AutoSize = true;
            this.lblPicovoiceKey.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.lblPicovoiceKey.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(142)))), ((int)(((byte)(142)))), ((int)(((byte)(147)))));
            this.lblPicovoiceKey.Location = new System.Drawing.Point(20, 45);
            this.lblPicovoiceKey.Name = "lblPicovoiceKey";
            this.lblPicovoiceKey.Size = new System.Drawing.Size(136, 15);
            this.lblPicovoiceKey.TabIndex = 1;
            this.lblPicovoiceKey.Text = "Введіть ваш Access Key:";
            // 
            // lblAPITitle
            // 
            this.lblAPITitle.AutoSize = true;
            this.lblAPITitle.Font = new System.Drawing.Font("Segoe UI Semibold", 10F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.lblAPITitle.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(242)))), ((int)(((byte)(242)))), ((int)(((byte)(247)))));
            this.lblAPITitle.Location = new System.Drawing.Point(15, 12);
            this.lblAPITitle.Name = "lblAPITitle";
            this.lblAPITitle.Size = new System.Drawing.Size(118, 19);
            this.lblAPITitle.TabIndex = 0;
            this.lblAPITitle.Text = "🔑 Picovoice API";
            // 
            // panelJarvis
            // 
            this.panelJarvis.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(45)))), ((int)(((byte)(50)))), ((int)(((byte)(55)))));
            this.panelJarvis.Controls.Add(this.btnSelectJarvis);
            this.panelJarvis.Controls.Add(this.lblJarvisPath);
            this.panelJarvis.Controls.Add(this.lblJarvisLabel);
            this.panelJarvis.Controls.Add(this.lblJarvisTitle);
            this.panelJarvis.Dock = System.Windows.Forms.DockStyle.Top;
            this.panelJarvis.Location = new System.Drawing.Point(0, 0);
            this.panelJarvis.Name = "panelJarvis";
            this.panelJarvis.Size = new System.Drawing.Size(575, 110);
            this.panelJarvis.TabIndex = 0;
            this.panelJarvis.Paint += new System.Windows.Forms.PaintEventHandler(this.panelCard_Paint);
            // 
            // btnSelectJarvis
            // 
            this.btnSelectJarvis.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(95)))), ((int)(((byte)(135)))), ((int)(((byte)(165)))));
            this.btnSelectJarvis.Cursor = System.Windows.Forms.Cursors.Hand;
            this.btnSelectJarvis.FlatAppearance.BorderSize = 0;
            this.btnSelectJarvis.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnSelectJarvis.Font = new System.Drawing.Font("Segoe UI Semibold", 9F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.btnSelectJarvis.ForeColor = System.Drawing.Color.White;
            this.btnSelectJarvis.Location = new System.Drawing.Point(20, 75);
            this.btnSelectJarvis.Name = "btnSelectJarvis";
            this.btnSelectJarvis.Size = new System.Drawing.Size(130, 25);
            this.btnSelectJarvis.TabIndex = 3;
            this.btnSelectJarvis.Text = "Вибрати файл";
            this.btnSelectJarvis.UseVisualStyleBackColor = false;
            this.btnSelectJarvis.MouseEnter += new System.EventHandler(this.Button_MouseEnter);
            this.btnSelectJarvis.MouseLeave += new System.EventHandler(this.Button_MouseLeave);
            // 
            // lblJarvisPath
            // 
            this.lblJarvisPath.Anchor = ((System.Windows.Forms.AnchorStyles)(((System.Windows.Forms.AnchorStyles.Top | System.Windows.Forms.AnchorStyles.Left) 
            | System.Windows.Forms.AnchorStyles.Right)));
            this.lblJarvisPath.Font = new System.Drawing.Font("Segoe UI", 8F, System.Drawing.FontStyle.Italic, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.lblJarvisPath.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(142)))), ((int)(((byte)(142)))), ((int)(((byte)(147)))));
            this.lblJarvisPath.Location = new System.Drawing.Point(20, 60);
            this.lblJarvisPath.Name = "lblJarvisPath";
            this.lblJarvisPath.Size = new System.Drawing.Size(535, 13);
            this.lblJarvisPath.TabIndex = 2;
            this.lblJarvisPath.Text = "Шлях не вибрано";
            this.lblJarvisPath.Click += new System.EventHandler(this.lblJarvisPath_Click);
            // 
            // lblJarvisLabel
            // 
            this.lblJarvisLabel.AutoSize = true;
            this.lblJarvisLabel.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.lblJarvisLabel.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(142)))), ((int)(((byte)(142)))), ((int)(((byte)(147)))));
            this.lblJarvisLabel.Location = new System.Drawing.Point(20, 40);
            this.lblJarvisLabel.Name = "lblJarvisLabel";
            this.lblJarvisLabel.Size = new System.Drawing.Size(196, 15);
            this.lblJarvisLabel.TabIndex = 1;
            this.lblJarvisLabel.Text = "Виберіть виконуваний файл Jarvis:";
            // 
            // lblJarvisTitle
            // 
            this.lblJarvisTitle.AutoSize = true;
            this.lblJarvisTitle.Font = new System.Drawing.Font("Segoe UI Semibold", 10F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.lblJarvisTitle.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(242)))), ((int)(((byte)(242)))), ((int)(((byte)(247)))));
            this.lblJarvisTitle.Location = new System.Drawing.Point(15, 12);
            this.lblJarvisTitle.Name = "lblJarvisTitle";
            this.lblJarvisTitle.Size = new System.Drawing.Size(129, 19);
            this.lblJarvisTitle.TabIndex = 0;
            this.lblJarvisTitle.Text = "📂 Шлях до Jarvis";
            // 
            // panelFooter
            // 
            this.panelFooter.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(45)))), ((int)(((byte)(50)))), ((int)(((byte)(55)))));
            this.panelFooter.Controls.Add(this.btnManageCommands);
            this.panelFooter.Controls.Add(this.btnSaveAndRestart);
            this.panelFooter.Controls.Add(this.btnSave);
            this.panelFooter.Dock = System.Windows.Forms.DockStyle.Bottom;
            this.panelFooter.Location = new System.Drawing.Point(0, 520);
            this.panelFooter.Name = "panelFooter";
            this.panelFooter.Padding = new System.Windows.Forms.Padding(20, 12, 20, 12);
            this.panelFooter.Size = new System.Drawing.Size(1200, 60);
            this.panelFooter.TabIndex = 2;
            // 
            // btnManageCommands
            // 
            this.btnManageCommands.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Right)));
            this.btnManageCommands.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(110)))), ((int)(((byte)(140)))), ((int)(((byte)(170)))));
            this.btnManageCommands.Cursor = System.Windows.Forms.Cursors.Hand;
            this.btnManageCommands.FlatAppearance.BorderSize = 0;
            this.btnManageCommands.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnManageCommands.Font = new System.Drawing.Font("Segoe UI Semibold", 9F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.btnManageCommands.ForeColor = System.Drawing.Color.White;
            this.btnManageCommands.Location = new System.Drawing.Point(995, 15);
            this.btnManageCommands.Name = "btnManageCommands";
            this.btnManageCommands.Size = new System.Drawing.Size(185, 32);
            this.btnManageCommands.TabIndex = 2;
            this.btnManageCommands.Text = "📋 Управління командами";
            this.btnManageCommands.UseVisualStyleBackColor = false;
            this.btnManageCommands.MouseEnter += new System.EventHandler(this.Button_MouseEnter);
            this.btnManageCommands.MouseLeave += new System.EventHandler(this.Button_MouseLeave);
            // 
            // btnSaveAndRestart
            // 
            this.btnSaveAndRestart.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left)));
            this.btnSaveAndRestart.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(95)))), ((int)(((byte)(135)))), ((int)(((byte)(165)))));
            this.btnSaveAndRestart.Cursor = System.Windows.Forms.Cursors.Hand;
            this.btnSaveAndRestart.FlatAppearance.BorderSize = 0;
            this.btnSaveAndRestart.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnSaveAndRestart.Font = new System.Drawing.Font("Segoe UI Semibold", 9F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.btnSaveAndRestart.ForeColor = System.Drawing.Color.White;
            this.btnSaveAndRestart.Location = new System.Drawing.Point(145, 15);
            this.btnSaveAndRestart.Name = "btnSaveAndRestart";
            this.btnSaveAndRestart.Size = new System.Drawing.Size(220, 32);
            this.btnSaveAndRestart.TabIndex = 1;
            this.btnSaveAndRestart.Text = "🔄 Зберегти і перезапустити";
            this.btnSaveAndRestart.UseVisualStyleBackColor = false;
            this.btnSaveAndRestart.MouseEnter += new System.EventHandler(this.Button_MouseEnter);
            this.btnSaveAndRestart.MouseLeave += new System.EventHandler(this.Button_MouseLeave);
            // 
            // btnSave
            // 
            this.btnSave.Anchor = ((System.Windows.Forms.AnchorStyles)((System.Windows.Forms.AnchorStyles.Bottom | System.Windows.Forms.AnchorStyles.Left)));
            this.btnSave.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(70)))), ((int)(((byte)(80)))), ((int)(((byte)(90)))));
            this.btnSave.Cursor = System.Windows.Forms.Cursors.Hand;
            this.btnSave.FlatAppearance.BorderSize = 0;
            this.btnSave.FlatStyle = System.Windows.Forms.FlatStyle.Flat;
            this.btnSave.Font = new System.Drawing.Font("Segoe UI Semibold", 9F, System.Drawing.FontStyle.Bold, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.btnSave.ForeColor = System.Drawing.Color.White;
            this.btnSave.Location = new System.Drawing.Point(20, 15);
            this.btnSave.Name = "btnSave";
            this.btnSave.Size = new System.Drawing.Size(110, 32);
            this.btnSave.TabIndex = 0;
            this.btnSave.Text = "💾 Зберегти";
            this.btnSave.UseVisualStyleBackColor = false;
            this.btnSave.MouseEnter += new System.EventHandler(this.Button_MouseEnter);
            this.btnSave.MouseLeave += new System.EventHandler(this.Button_MouseLeave);
            // 
            // Form1
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(7F, 15F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.BackColor = System.Drawing.Color.FromArgb(((int)(((byte)(35)))), ((int)(((byte)(40)))), ((int)(((byte)(45)))));
            this.ClientSize = new System.Drawing.Size(1200, 580);
            this.Controls.Add(this.panelMain);
            this.Controls.Add(this.panelFooter);
            this.Controls.Add(this.panelHeader);
            this.Font = new System.Drawing.Font("Segoe UI", 9F, System.Drawing.FontStyle.Regular, System.Drawing.GraphicsUnit.Point, ((byte)(204)));
            this.ForeColor = System.Drawing.Color.FromArgb(((int)(((byte)(242)))), ((int)(((byte)(242)))), ((int)(((byte)(247)))));
            this.MinimumSize = new System.Drawing.Size(1216, 619);
            this.Name = "Form1";
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
            this.Text = "Alexa Settings — Професійне налаштування";
            this.Load += new System.EventHandler(this.Form1_Load_1);
            this.panelHeader.ResumeLayout(false);
            this.panelHeader.PerformLayout();
            this.panelMain.ResumeLayout(false);
            this.panelRight.ResumeLayout(false);
            this.panelTiming.ResumeLayout(false);
            this.panelTiming.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.numSilenceDetectSeconds)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.numContinuousListenSeconds)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.numCommandSessionTimeout)).EndInit();
            this.panelSettings.ResumeLayout(false);
            this.panelSettings.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.trackSensitivity)).EndInit();
            this.panelLeft.ResumeLayout(false);
            this.panelWakeWord.ResumeLayout(false);
            this.panelWakeWord.PerformLayout();
            this.panelAPI.ResumeLayout(false);
            this.panelAPI.PerformLayout();
            this.panelJarvis.ResumeLayout(false);
            this.panelJarvis.PerformLayout();
            this.panelFooter.ResumeLayout(false);
            this.ResumeLayout(false);

        }

        #endregion

        private System.Windows.Forms.Panel panelHeader;
        private System.Windows.Forms.Label lblTitle;
        private System.Windows.Forms.Label lblSubtitle;
        private System.Windows.Forms.Panel panelMain;
        private System.Windows.Forms.Panel panelLeft;
        private System.Windows.Forms.Panel panelJarvis;
        private System.Windows.Forms.Label lblJarvisTitle;
        private System.Windows.Forms.Label lblJarvisLabel;
        private System.Windows.Forms.Label lblJarvisPath;
        private System.Windows.Forms.Button btnSelectJarvis;
        private System.Windows.Forms.Panel panelAPI;
        private System.Windows.Forms.Label lblAPITitle;
        private System.Windows.Forms.Label lblPicovoiceKey;
        private System.Windows.Forms.TextBox txtPicovoiceKey;
        private System.Windows.Forms.Button btnPicovoiceWebsite;
        private System.Windows.Forms.Button btnPicovoiceHelp;
        private System.Windows.Forms.Panel panelWakeWord;
        private System.Windows.Forms.Label lblWakeWordTitle;
        private System.Windows.Forms.RadioButton radioStandard;
        private System.Windows.Forms.RadioButton radioCustom;
        private System.Windows.Forms.ComboBox cmbWakeWord;
        private System.Windows.Forms.Label lblCustomWakeWordPath;
        private System.Windows.Forms.TextBox txtCustomWakeWordPath;
        private System.Windows.Forms.Button btnBrowseCustomWakeWord;
        private System.Windows.Forms.Panel panelRight;
        private System.Windows.Forms.Panel panelSettings;
        private System.Windows.Forms.Label lblSettingsTitle;
        private System.Windows.Forms.Label lblLanguage;
        private System.Windows.Forms.ComboBox cmbLanguage;
        private System.Windows.Forms.Label lblSensitivity;
        private System.Windows.Forms.Label lblSensitivityValue;
        private System.Windows.Forms.TrackBar trackSensitivity;
        private System.Windows.Forms.Panel panelTiming;
        private System.Windows.Forms.Label lblTimingTitle;
        private System.Windows.Forms.Label lblCommandSessionTimeout;
        private System.Windows.Forms.Label lblContinuousListenSeconds;
        private System.Windows.Forms.Label lblSilenceDetectSeconds;
        private System.Windows.Forms.NumericUpDown numCommandSessionTimeout;
        private System.Windows.Forms.NumericUpDown numContinuousListenSeconds;
        private System.Windows.Forms.NumericUpDown numSilenceDetectSeconds;
        private System.Windows.Forms.Panel panelFooter;
        private System.Windows.Forms.Button btnSave;
        private System.Windows.Forms.Button btnSaveAndRestart;
        private System.Windows.Forms.Button btnManageCommands;
    }
}