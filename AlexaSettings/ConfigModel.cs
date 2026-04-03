using Newtonsoft.Json;

namespace AlexaSettings
{
    public class ConfigModel
    {
        [JsonProperty("picovoiceAccessKey")]
        public string PicovoiceAccessKey { get; set; } = "";

        [JsonProperty("wakeWordStandard")]
        public string WakeWordStandard { get; set; } = "alexa";

        [JsonProperty("sensitivity")]
        public double Sensitivity { get; set; } = 0.5;

        // Список активних мов для розпізнавання (масив, наприклад ["uk-UA","en-US"])
        [JsonProperty("languages")]
        public List<string> Languages { get; set; } = new List<string> { "uk-UA", "ru-RU", "en-US" };

        [JsonProperty("wakeWordMode")]
        public string WakeWordMode { get; set; } = "standard";

        [JsonProperty("customWakeWordPath")]
        public string CustomWakeWordPath { get; set; } = "";

        [JsonProperty("commandSessionTimeout")]
        public int CommandSessionTimeout { get; set; } = 15;

        [JsonProperty("continuousListenSeconds")]
        public int ContinuousListenSeconds { get; set; } = 7;

        [JsonProperty("silenceDetectSeconds")]
        public double SilenceDetectSeconds { get; set; } = 2.0;

        [JsonProperty("silenceTimeout")]
        public double SilenceTimeout { get; set; } = 6.0;

        [JsonProperty("openaiApiKey")]
        public string OpenaiApiKey { get; set; } = "";

        [JsonProperty("ttsEnabled")]
        public bool TtsEnabled { get; set; } = true;

        [JsonProperty("ttsVoice")]
        public string TtsVoice { get; set; } = "jarvis";

        [JsonProperty("ttsRate")]
        public string TtsRate { get; set; } = "+25%";

        [JsonProperty("microphoneDevice")]
        public string MicrophoneDevice { get; set; } = "";

        [JsonProperty("microphoneVolume")]
        public int MicrophoneVolume { get; set; } = -1; // -1 = не задано (зберігати системне)

        [JsonProperty("useGeminiSTT")]
        public bool UseGeminiSTT { get; set; } = false;

        [JsonProperty("routingModel")]
        public string RoutingModel { get; set; } = "";

        [JsonProperty("pluginModel")]
        public string PluginModel { get; set; } = "";

        [JsonProperty("disabledPlugins")]
        public List<string> DisabledPlugins { get; set; } = new List<string>();
    }

    // ─── Метадані плагіна ────────────────────────────────────────────────────────
    public class PluginInfo
    {
        public string PluginName  { get; set; } = "";
        public string Description { get; set; } = "";
        public Dictionary<string, string> Commands { get; set; } = new();
    }

    /// <summary>
    /// Читає метадані плагінів прямо з .py файлів — шукає name, description та commands.
    /// Нові плагіни підхоплюються автоматично.
    /// </summary>
    public static class PluginParser
    {
        /// <summary>Знаходить папку plugins/ відносно AlexaSettings.exe (або репо).</summary>
        public static string FindPluginsDir()
        {
            string dir = AppDomain.CurrentDomain.BaseDirectory;
            for (int i = 0; i < 6; i++)
            {
                string candidate = Path.Combine(dir, "plugins");
                if (Directory.Exists(candidate))
                    return candidate;
                dir = Path.GetDirectoryName(dir) ?? dir;
            }
            return "";
        }

        /// <summary>Парсить один .py файл і повертає PluginInfo або null.</summary>
        public static PluginInfo? ParseFile(string path)
        {
            try
            {
                var lines = File.ReadAllLines(path, System.Text.Encoding.UTF8);
                var info = new PluginInfo();

                for (int i = 0; i < lines.Length; i++)
                {
                    string trimmed = lines[i].Trim();

                    // def name(self) → наступний рядок return "..."
                    if (trimmed == "def name(self) -> str:" && i + 1 < lines.Length)
                    {
                        info.PluginName = ExtractReturn(lines[i + 1]);
                    }

                    // def description(self) → наступний рядок return "..."
                    if (trimmed == "def description(self) -> str:" && i + 1 < lines.Length)
                    {
                        info.Description = ExtractReturn(lines[i + 1]);
                    }

                    // def commands(self) → шукаємо return { ... }
                    if (trimmed == "def commands(self) -> Dict[str, str]:")
                    {
                        // Знаходимо перший рядок "return {"
                        for (int j = i + 1; j < lines.Length && j < i + 5; j++)
                        {
                            if (lines[j].Trim() == "return {")
                            {
                                // Читаємо до закриваючої дужки
                                for (int k = j + 1; k < lines.Length; k++)
                                {
                                    string cl = lines[k].Trim();
                                    if (cl == "}" || cl.StartsWith("}")) break;
                                    // "cmd_name": "опис..."  або  'cmd_name': 'опис...'
                                    var m = System.Text.RegularExpressions.Regex.Match(
                                        cl, @"[""'](\w+)[""']\s*:\s*[""'](.*?)[""'],?\s*$");
                                    if (m.Success)
                                        info.Commands[m.Groups[1].Value] = m.Groups[2].Value;
                                }
                                break;
                            }
                        }
                    }
                }

                return string.IsNullOrEmpty(info.PluginName) ? null : info;
            }
            catch { return null; }
        }

        private static string ExtractReturn(string line)
        {
            var m = System.Text.RegularExpressions.Regex.Match(line.Trim(), @"^return\s+[""'](.*)[""']$");
            return m.Success ? m.Groups[1].Value : "";
        }

        /// <summary>Сканує папку plugins/ і повертає список PluginInfo, відсортований за PluginName.</summary>
        public static List<PluginInfo> LoadAll()
        {
            var result = new List<PluginInfo>();
            string dir = FindPluginsDir();
            if (!Directory.Exists(dir)) return result;

            foreach (var file in Directory.GetFiles(dir, "*.py").OrderBy(f => Path.GetFileNameWithoutExtension(f)))
            {
                string fname = Path.GetFileNameWithoutExtension(file);
                if (fname == "base_plugin" || fname.StartsWith("_")) continue;

                var info = ParseFile(file);
                if (info != null)
                    result.Add(info);
            }
            return result;
        }
    }

    // ─── Допоміжні моделі для UI ─────────────────────────────────────────────────

    // Допоміжна модель для відображення мов у UI
    public static class LanguageOptions
    {
        public static readonly Dictionary<string, string> All = new()
        {
            { "uk-UA", "Українська" },
            { "en-US", "English (США)" },
            { "ru-RU", "Русский" },
            { "pl-PL", "Polski" },
            { "de-DE", "Deutsch" },
            { "fr-FR", "Français" },
        };
    }

    // Допоміжна модель для відображення голосів у UI
    public static class VoiceOptions
    {
        // Внутрішній ключ (ttsVoice в config) → відображувана назва
        public static readonly Dictionary<string, string> All = new()
        {
            { "jarvis",              "Остап (чоловічий, UK) — Jarvis" },
            { "ostap",               "Остап (чоловічий, UK)" },
            { "polina",              "Поліна (жіночий, UK)" },
            { "uk-UA-OstapNeural",   "Остап Neural (чоловічий, UK)" },
            { "uk-UA-PolinaNeural",  "Поліна Neural (жіночий, UK)" },
            { "en-US-GuyNeural",     "Guy (чоловічий, EN)" },
            { "en-US-JennyNeural",   "Jenny (жіночий, EN)" },
        };
    }
}
