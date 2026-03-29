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
    }

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
