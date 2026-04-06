using Newtonsoft.Json;

namespace AlexaSettingsWinUI.Models;

public static class ConfigLocator
{
    public static string Find()
    {
        string dir = AppDomain.CurrentDomain.BaseDirectory;
        for (int i = 0; i < 6; i++)
        {
            string candidate = Path.Combine(dir, "config.json");
            if (File.Exists(candidate)) return candidate;
            dir = Path.GetDirectoryName(dir) ?? dir;
        }
        return Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "config.json");
    }
}

public static class ConfigLoader
{
    public static ConfigModel Load(string path)
    {
        if (!File.Exists(path)) return new ConfigModel();
        try
        {
            var json = File.ReadAllText(path);
            return JsonConvert.DeserializeObject<ConfigModel>(json) ?? new ConfigModel();
        }
        catch { return new ConfigModel(); }
    }

    public static bool Save(string path, ConfigModel config)
    {
        try
        {
            var json = JsonConvert.SerializeObject(config, Formatting.Indented);
            File.WriteAllText(path, json);
            return true;
        }
        catch { return false; }
    }
}

public static class PluginParser
{
    public static string FindPluginsDir()
    {
        string dir = AppDomain.CurrentDomain.BaseDirectory;
        for (int i = 0; i < 6; i++)
        {
            string candidate = Path.Combine(dir, "plugins");
            if (Directory.Exists(candidate)) return candidate;
            dir = Path.GetDirectoryName(dir) ?? dir;
        }
        return "";
    }

    public static List<PluginInfo> LoadAll()
    {
        var result = new List<PluginInfo>();
        string dir = FindPluginsDir();
        if (!Directory.Exists(dir)) return result;

        foreach (var file in Directory.GetFiles(dir, "*.py").OrderBy(Path.GetFileNameWithoutExtension))
        {
            string fname = Path.GetFileNameWithoutExtension(file);
            if (fname == "base_plugin" || fname.StartsWith('_')) continue;
            var info = ParseFile(file);
            if (info != null) result.Add(info);
        }
        return result;
    }

    private static PluginInfo? ParseFile(string path)
    {
        try
        {
            var lines = File.ReadAllLines(path, System.Text.Encoding.UTF8);
            var info = new PluginInfo();

            for (int i = 0; i < lines.Length; i++)
            {
                string t = lines[i].Trim();

                if (t == "def name(self) -> str:" && i + 1 < lines.Length)
                    info.PluginName = ExtractReturn(lines[i + 1]);

                if (t == "def description(self) -> str:" && i + 1 < lines.Length)
                    info.Description = ExtractReturn(lines[i + 1]);

                if (t == "def commands(self) -> Dict[str, str]:")
                {
                    for (int j = i + 1; j < lines.Length && j < i + 5; j++)
                    {
                        if (lines[j].Trim() == "return {")
                        {
                            for (int k = j + 1; k < lines.Length; k++)
                            {
                                string cl = lines[k].Trim();
                                if (cl == "}" || cl.StartsWith('}')) break;
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
}
