# Alex

A Windows voice assistant with hot-pluggable skills. Say the wake word, ask for
something in plain language, and a model decides which of ~17 plugins should
handle it.

Python for the assistant itself, C# for two desktop settings applications.
Ships as a packaged executable with a tray icon.

## What it can do

Window and monitor management, per-application volume, media control, screen
vision, news and web search, calendar reading, entertainment and film
suggestions, keyboard automation, system monitoring, and a plugin for Ukrainian
power blackout schedules.

Each of those is a plugin. Adding a new one means dropping a file into
`plugins/` — no changes to the assistant's core.

## How a request flows

1. **Porcupine** detects the wake word offline, so nothing is streamed until
   you actually address the assistant
2. Audio goes to speech-to-text
3. **Gemini** receives the transcript along with every plugin exposed as a
   function declaration, and picks what to call
4. The plugin runs, the assistant speaks the result

## Two mechanisms worth explaining

### Speaking before the work is done

Every plugin is auto-converted into a Gemini `FunctionDeclaration`. Alongside
them sits one synthetic tool, `speak_response(text, is_command, transcript)`,
and the model is instructed to **always call it together with** the real
command.

The streaming reader runs the blocking SDK stream in an executor thread feeding
an `asyncio.Queue`. The moment the `speak_response` part arrives — before the
rest of the response has finished streaming, before the actual plugin has run —
an `on_speak_ready` callback fires and text-to-speech starts talking.

So one model round trip produces both the spoken acknowledgement and the
action, and the acknowledgement is heard while the action is still being
parsed and executed. The assistant answers immediately instead of pausing for
the whole pipeline.

### Plugins that install their own dependencies

A plugin dropped into `plugins/` may import something that is not installed.
Rather than failing, `smart_plugin_manager.py` recovers:

1. Catch the `ImportError` and extract the missing module name
2. Map it through a pip alias table — `win32gui` is not a package, `pywin32` is
3. Locate the **system** Python, which is not trivial when running frozen under
   PyInstaller where `sys.executable` points at `Alex.exe`
4. Install with `CREATE_NO_WINDOW`, so no console window flashes at the user
5. Run `pywin32_postinstall` when that particular package needs its DLLs
   registered
6. Inject system site-packages into `sys.path` and retry the import

The result is that a user can add a third-party plugin and it works on first
load, without being told to open a terminal.

## Plugin interface

A plugin subclasses `SmartPlugin` and declares a name, a one-line description
for the model, and a dict of commands. The description matters more than it
looks — it is what the model reads when deciding whether this plugin is the
right one for a request.

```python
class MyPlugin(SmartPlugin):
    @property
    def name(self) -> str: ...

    @property
    def description(self) -> str: ...   # 1-2 sentences, read by the model

    @property
    def commands(self) -> Dict[str, str]: ...
```

## Settings applications

Two separate C# front-ends: an older WinForms one and a newer WinUI 3 version
with an icon grid for managing plugins. Both edit the same local configuration
the Python side reads.

## Configuration

Keys live in a local `config.json` that is gitignored — a Picovoice access key
for the wake word, and a Gemini key. The assistant refuses to start on
placeholder values rather than failing later with a confusing error.

## Building

```bash
pip install -r requirements.txt
python main.py          # run from source
python build.py         # package with PyInstaller
```
