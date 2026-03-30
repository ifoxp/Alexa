"""
build.py — збірка Alexa Assistant
Що робить:
  1. Збирає Python додаток через PyInstaller → dist/Alexa/Alexa.exe
  2. Збирає C# AlexaSettings через dotnet publish → dist/Alexa/AlexaSettings.exe
  3. Копіює config.json, assets/, plugins/ в dist/Alexa/
  4. Прибирає тимчасові файли build/ та .spec

Результат: папка dist/Alexa/ — готова до запуску, config.json вже там.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# Fix encoding for Windows console
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# ─── Налаштування ─────────────────────────────────────────────────────────────
EXE_NAME        = "Alexa"
MAIN_SCRIPT     = "main.py"
CSHARP_DIR      = Path(__file__).resolve().parent / "AlexaSettings"
CSHARP_EXE_NAME = "AlexaSettings.exe"

BASE_DIR   = Path(__file__).resolve().parent
DIST_DIR   = BASE_DIR / "dist" / EXE_NAME
ICON_FILE  = BASE_DIR / "assets" / "jarvis.ico"
# ──────────────────────────────────────────────────────────────────────────────


def step(n: int, total: int, msg: str):
    print(f"\n[{n}/{total}] {msg}")


def get_package_path(package_name: str) -> Path | None:
    try:
        import importlib.util
        spec = importlib.util.find_spec(package_name)
        if spec and spec.origin:
            return Path(spec.origin).parent
    except Exception:
        pass
    return None


# ─── Крок 1: Збірка Python (PyInstaller) ──────────────────────────────────────
def build_python() -> bool:
    step(1, 4, "Збірка Python → PyInstaller")

    pvporcupine_path = get_package_path("pvporcupine")
    if not pvporcupine_path:
        print("  [ПОМИЛКА] Пакет pvporcupine не знайдено.")
        return False

    pv_lib       = pvporcupine_path / "lib"
    pv_resources = pvporcupine_path / "resources"


    if not pv_lib.exists() or not pv_resources.exists():
        print("  [ПОМИЛКА] Папки lib/resources всередині pvporcupine не знайдено.")
        return False

    if not ICON_FILE.exists():
        print(f"  [ПОМИЛКА] Іконка не знайдена: {ICON_FILE}")
        return False

    local_modules = [
        'audio_buffer', 'memory_manager', 'wake_word', 'tray_manager',
        'smart_ai', 'config_manager', 'logger_config', 'command_manager',
        'command_logger', 'transcriber', 'audio_player',
        'smart_plugin_manager', 'settings', 'media_controller',
    ]

    cmd = [
        'pyinstaller',
        '--onedir',
        f'--name={EXE_NAME}',
        f'--icon={ICON_FILE}',
        f'--add-data={pv_lib}{os.pathsep}pvporcupine/lib',
        f'--add-data={pv_resources}{os.pathsep}pvporcupine/resources',
        f'--add-data=assets{os.pathsep}assets',
        f'--add-data=plugins{os.pathsep}plugins',
        '--hidden-import=pyaudio',
        '--hidden-import=pvporcupine',
        '--hidden-import=pystray',
        '--hidden-import=PIL',
        # spotipy — використовується в music_control.py
        '--hidden-import=spotipy',
        '--hidden-import=spotipy.oauth2',
        '--hidden-import=spotipy.cache_handler',
        # pycaw — використовується в main.py та sound_control.py
        '--hidden-import=pycaw',
        '--hidden-import=pycaw.pycaw',
        '--hidden-import=pycaw.utils',
        # psutil — використовується в media_controller.py та sound_control.py
        '--hidden-import=psutil',
        # pywin32 — тільки ті модулі що реально імпортуються в коді:
        # win32gui, win32process (sound_control.py), comtypes (main.py, sound_control.py)
        '--hidden-import=win32gui',
        '--hidden-import=win32process',
        '--hidden-import=comtypes',
        '--hidden-import=comtypes.client',
        '--hidden-import=pywintypes',
        # winsdk — media_controller.py
        '--hidden-import=winsdk',
        '--hidden-import=winsdk.windows.media.control',
        # інші плагіни
        '--hidden-import=keyboard',
        '--hidden-import=screen_brightness_control',
        # mss, pyautogui, pyperclip — screen_vision.py
        '--hidden-import=mss',
        '--hidden-import=mss.tools',
        '--hidden-import=pyautogui',
        '--hidden-import=pyperclip',
        # google-genai — Gemini SDK
        '--hidden-import=google.genai',
        '--hidden-import=google.genai.types',
        '--hidden-import=google.auth',
        '--hidden-import=google.auth.transport.requests',
        # google-calendar — calendar_reader.py
        '--hidden-import=google.oauth2.credentials',
        '--hidden-import=google_auth_oauthlib.flow',
        '--hidden-import=googleapiclient.discovery',
        '--hidden-import=googleapiclient',
        '--hidden-import=google_auth_httplib2',
        # Виключаємо наукові бібліотеки — в проекті не використовуються
        '--exclude-module=numpy',
        '--exclude-module=scipy',
        '--exclude-module=matplotlib',
        '--exclude-module=pandas',
        '--exclude-module=tkinter',
        '--noconsole',
    ]

    for mod in local_modules:
        py_file = BASE_DIR / f"{mod}.py"
        if py_file.exists():
            cmd += [f'--add-data={py_file}{os.pathsep}.', f'--hidden-import={mod}']

    cmd.append(MAIN_SCRIPT)

    # Чистимо стару збірку
    old = BASE_DIR / "dist" / EXE_NAME
    if old.exists():
        shutil.rmtree(old, ignore_errors=True)

    print(f"  Запуск PyInstaller...")
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding='utf-8', errors='replace'
    )
    for line in proc.stdout:
        print(" ", line.rstrip())
    proc.wait()

    if proc.returncode != 0:
        print(f"  [ПОМИЛКА] PyInstaller завершився з кодом {proc.returncode}")
        return False

    print("  [OK] Python EXE зібрано.")
    return True


# ─── Крок 2: Збірка C# (dotnet publish) ───────────────────────────────────────
def build_csharp() -> bool:
    step(2, 4, "Збірка C# AlexaSettings → dotnet publish")

    csproj = CSHARP_DIR / "AlexaSettings.csproj"
    if not csproj.exists():
        print(f"  [ПОМИЛКА] .csproj не знайдено: {csproj}")
        return False

    publish_dir = CSHARP_DIR / "bin" / "publish"

    cmd = [
        'dotnet', 'publish', str(csproj),
        '-c', 'Release',
        '-r', 'win-x64',
        '--self-contained', 'false',
        f'-o', str(publish_dir),
        '/p:PublishSingleFile=true',
        '/p:IncludeNativeLibrariesForSelfExtract=true',
    ]

    print("  Запуск dotnet publish...")
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if proc.returncode != 0:
        print(f"  [ПОМИЛКА] dotnet publish завершився з кодом {proc.returncode}")
        print(proc.stderr[-2000:] if proc.stderr else "")
        return False

    # Копіюємо AlexaSettings.exe в dist/Alexa/
    src_exe = publish_dir / CSHARP_EXE_NAME
    if not src_exe.exists():
        # dotnet може назвати по-різному
        exes = list(publish_dir.glob("*.exe"))
        src_exe = exes[0] if exes else None

    if not src_exe or not src_exe.exists():
        print(f"  [ПОМИЛКА] {CSHARP_EXE_NAME} не знайдено в {publish_dir}")
        return False

    DIST_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src_exe, DIST_DIR / CSHARP_EXE_NAME)
    print(f"  [OK] {CSHARP_EXE_NAME} скопійовано в dist/{EXE_NAME}/")
    return True


# ─── Крок 3: Копіювання config.json, assets, plugins ─────────────────────────
def copy_extra_files():
    step(3, 4, "Копіювання config.json, assets/, plugins/")

    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # config.json — НЕ перезаписуємо якщо вже є (щоб не затерти налаштування)
    src_cfg = BASE_DIR / "config.json"
    dst_cfg = DIST_DIR / "config.json"
    if src_cfg.exists() and not dst_cfg.exists():
        shutil.copy2(src_cfg, dst_cfg)
        print("  [OK] config.json скопійовано")
    elif dst_cfg.exists():
        print("  [--] config.json вже є в dist, не перезаписуємо")
    else:
        print("  [УВАГА] config.json не знайдено в корені проєкту")

    # assets/
    src_assets = BASE_DIR / "assets"
    dst_assets = DIST_DIR / "assets"
    if src_assets.exists():
        if dst_assets.exists():
            shutil.rmtree(dst_assets)
        shutil.copytree(src_assets, dst_assets)
        print(f"  [OK] assets/ скопійовано ({len(list(dst_assets.rglob('*')))} файлів)")
    else:
        print("  [УВАГА] assets/ не знайдено")

    # plugins/
    src_plugins = BASE_DIR / "plugins"
    dst_plugins = DIST_DIR / "plugins"
    if src_plugins.exists():
        if dst_plugins.exists():
            shutil.rmtree(dst_plugins)
        shutil.copytree(src_plugins, dst_plugins)
        print(f"  [OK] plugins/ скопійовано ({len(list(src_plugins.glob('*.py')))} плагінів)")
    else:
        print("  [УВАГА] plugins/ не знайдено")

    # .spotify_cache — НЕ перезаписуємо якщо вже є (щоб не затерти токен)
    src_cache = BASE_DIR / ".spotify_cache"
    dst_cache = DIST_DIR / ".spotify_cache"
    if src_cache.exists() and not dst_cache.exists():
        shutil.copy2(src_cache, dst_cache)
        print("  [OK] .spotify_cache скопійовано")

    # credentials.json (Ключі Google API)
    src_creds = BASE_DIR / "credentials.json"
    dst_creds = DIST_DIR / "credentials.json"
    if src_creds.exists() and not dst_creds.exists():
        shutil.copy2(src_creds, dst_creds)
        print("  [OK] credentials.json скопійовано")

    # .calendar_state.json (Пам'ять календаря)
    src_cal_state = BASE_DIR / ".calendar_state.json"
    dst_cal_state = DIST_DIR / ".calendar_state.json"
    if src_cal_state.exists() and not dst_cal_state.exists():
        shutil.copy2(src_cal_state, dst_cal_state)
        print("  [OK] .calendar_state.json скопійовано")

    # schedule.json (Графік відключень світла для blackout_schedule плагіна)
    src_schedule = BASE_DIR / "schedule.json"
    dst_schedule = DIST_DIR / "schedule.json"
    if src_schedule.exists() and not dst_schedule.exists():
        shutil.copy2(src_schedule, dst_schedule)
        print("  [OK] schedule.json скопійовано")
    elif src_schedule.exists():
        print("  [--] schedule.json вже є в dist, не перезаписуємо")

    # calendar_tokens/ (Збережені авторизації)
    src_tokens = BASE_DIR / "calendar_tokens"
    dst_tokens = DIST_DIR / "calendar_tokens"
    if src_tokens.exists():
        if not dst_tokens.exists():
            shutil.copytree(src_tokens, dst_tokens)
            print("  [OK] calendar_tokens/ скопійовано")
        else:
            print("  [--] calendar_tokens/ вже є, пропускаємо щоб не затерти")
# ─── Крок 4: Очищення тимчасових файлів ──────────────────────────────────────
def cleanup():
    step(4, 4, "Очищення тимчасових файлів")
    shutil.rmtree(BASE_DIR / "build", ignore_errors=True)
    spec = BASE_DIR / f"{EXE_NAME}.spec"
    if spec.exists():
        spec.unlink()
    print("  [OK] Тимчасові файли видалено.")


# ─── Точка входу ──────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Alexa Assistant — білд")
    print("=" * 60)

    if not build_python():
        print("\n[ЗУПИНЕНО] Помилка збірки Python.")
        sys.exit(1)

    if not build_csharp():
        print("\n[УВАГА] C# не зібрано, продовжуємо без AlexaSettings.exe")

    copy_extra_files()
    cleanup()

    print("\n" + "=" * 60)
    print("  ГОТОВО!")
    print(f"  Папка: dist/{EXE_NAME}/")
    print(f"  Асистент:    dist/{EXE_NAME}/{EXE_NAME}.exe")
    print(f"  Налаштування: dist/{EXE_NAME}/{CSHARP_EXE_NAME}")
    print(f"  Конфіг:      dist/{EXE_NAME}/config.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
