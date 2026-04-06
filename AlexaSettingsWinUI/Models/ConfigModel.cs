using Newtonsoft.Json;

namespace AlexaSettingsWinUI.Models;

public class ConfigModel
{
    [JsonProperty("picovoiceAccessKey")]  public string PicovoiceAccessKey    { get; set; } = "";
    [JsonProperty("wakeWordStandard")]    public string WakeWordStandard       { get; set; } = "alexa";
    [JsonProperty("wakeWordMode")]        public string WakeWordMode           { get; set; } = "standard";
    [JsonProperty("customWakeWordPath")] public string CustomWakeWordPath     { get; set; } = "";
    [JsonProperty("sensitivity")]         public double Sensitivity            { get; set; } = 0.5;
    [JsonProperty("languages")]           public List<string> Languages        { get; set; } = ["uk-UA", "ru-RU", "en-US"];
    [JsonProperty("commandSessionTimeout")]   public int CommandSessionTimeout   { get; set; } = 15;
    [JsonProperty("continuousListenSeconds")] public int ContinuousListenSeconds { get; set; } = 7;
    [JsonProperty("silenceDetectSeconds")]    public double SilenceDetectSeconds { get; set; } = 2.0;
    [JsonProperty("silenceTimeout")]          public double SilenceTimeout       { get; set; } = 6.0;
    [JsonProperty("openaiApiKey")]       public string OpenaiApiKey           { get; set; } = "";
    [JsonProperty("ttsEnabled")]         public bool   TtsEnabled             { get; set; } = true;
    [JsonProperty("ttsVoice")]           public string TtsVoice               { get; set; } = "jarvis";
    [JsonProperty("ttsRate")]            public string TtsRate                { get; set; } = "+25%";
    [JsonProperty("microphoneDevice")]   public string MicrophoneDevice       { get; set; } = "";
    [JsonProperty("microphoneVolume")]   public int    MicrophoneVolume       { get; set; } = -1;
    [JsonProperty("useGeminiSTT")]       public bool   UseGeminiSTT           { get; set; } = false;
    [JsonProperty("routingModel")]       public string RoutingModel           { get; set; } = "";
    [JsonProperty("pluginModel")]        public string PluginModel            { get; set; } = "";
    [JsonProperty("disabledPlugins")]    public List<string> DisabledPlugins  { get; set; } = [];
}

public class PluginInfo
{
    public string PluginName  { get; set; } = "";
    public string Description { get; set; } = "";
    public Dictionary<string, string> Commands { get; set; } = [];
}

public static class LanguageOptions
{
    public static readonly Dictionary<string, string> All = new()
    {
        { "uk-UA", "Українська"     },
        { "en-US", "English (США)"  },
        { "ru-RU", "Русский"        },
        { "pl-PL", "Polski"         },
        { "de-DE", "Deutsch"        },
        { "fr-FR", "Français"       },
    };
}

public static class VoiceOptions
{
    public static readonly Dictionary<string, string> All = new()
    {
        { "jarvis",             "Остап (чоловічий, UK) — Jarvis" },
        { "ostap",              "Остап (чоловічий, UK)"           },
        { "polina",             "Поліна (жіночий, UK)"            },
        { "uk-UA-OstapNeural",  "Остап Neural (чоловічий, UK)"    },
        { "uk-UA-PolinaNeural", "Поліна Neural (жіночий, UK)"     },
        { "en-US-GuyNeural",    "Guy (чоловічий, EN)"             },
        { "en-US-JennyNeural",  "Jenny (жіночий, EN)"             },
    };
}
