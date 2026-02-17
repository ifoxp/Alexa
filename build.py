import os
import sys
import shutil
import subprocess
from pathlib import Path

# --- НАЛАШТУВАННЯ БІЛДУ ---
EXE_NAME = "Alexa"
MAIN_SCRIPT = "main.py"
HIDE_CONSOLE = True
ASSETS_DIR = "assets"
PLUGINS_DIR = "plugins"

# --- ДИНАМІЧНІ ШЛЯХИ ---
BASE_DIR = Path(__file__).resolve().parent
ICON_FILE = BASE_DIR / ASSETS_DIR / "jarvis.ico"

def get_package_path(package_name):
    """Знаходить абсолютний шлях до встановленого пакету."""
    try:
        import importlib.util
        spec = importlib.util.find_spec(package_name)
        if spec and spec.origin:
            return Path(spec.origin).parent
        return None
    except Exception as e:
        print(f"[ПОМИЛКА] Помилка під час пошуку пакету {package_name}: {e}")
        return None

def copy_csharp_settings_app():
    """Копіює C# додаток налаштувань та його залежності в dist папку."""
    print("Копіювання C# налаштувань...")

    csharp_bin_dir = BASE_DIR / "AlexaS" / "AlexaS" / "bin" / "Release"
    csharp_exe = csharp_bin_dir / "AlexaS.exe"
    dist_dir = BASE_DIR / "dist"
    target_exe = dist_dir / "AlexaSettingsApp.exe"

    if not csharp_exe.exists():
        print(f"УВАГА: C# EXE не знайдено за шляхом: {csharp_exe}")
        print("   Спочатку збудуйте C# проект в Release режимі через Visual Studio")
        return False

    # Створюємо dist папку якщо не існує
    dist_dir.mkdir(exist_ok=True)

    # Копіюємо основний EXE
    shutil.copy2(csharp_exe, target_exe)
    print(f"OK: C# EXE скопійовано: {target_exe.name}")

    # Копіюємо всі DLL залежності
    dll_files = list(csharp_bin_dir.glob("*.dll"))
    copied_dlls = []

    for dll_file in dll_files:
        target_dll = dist_dir / dll_file.name
        shutil.copy2(dll_file, target_dll)
        copied_dlls.append(dll_file.name)

    if copied_dlls:
        print(f"OK: Скопійовано {len(copied_dlls)} DLL залежностей:")
        for dll in copied_dlls:
            print(f"   - {dll}")

    # Копіюємо config файл якщо є
    config_file = csharp_bin_dir / "AlexaS.exe.config"
    if config_file.exists():
        target_config = dist_dir / "AlexaSettingsApp.exe.config"
        shutil.copy2(config_file, target_config)
        print(f"OK: Config скопійовано: {target_config.name}")

    return True

def copy_plugins_folder():
    """Копіює папку plugins поруч з EXE для користувачів."""
    print("Копіювання папки plugins...")

    plugins_source = BASE_DIR / "plugins"
    dist_dir = BASE_DIR / "dist"
    plugins_target = dist_dir / "plugins"

    if not plugins_source.exists():
        print(f"УВАГА: Папка plugins не знайдена: {plugins_source}")
        return False

    # Створюємо dist папку якщо не існує
    dist_dir.mkdir(exist_ok=True)

    # Видаляємо стару папку plugins якщо існує
    if plugins_target.exists():
        shutil.rmtree(plugins_target)

    # Копіюємо всю папку plugins
    shutil.copytree(plugins_source, plugins_target)

    # Лічимо скільки файлів скопійовано
    plugin_files = list(plugins_target.glob("*.py"))
    print(f"OK: Скопійовано папку plugins з {len(plugin_files)} файлами:")
    for plugin_file in plugin_files:
        print(f"   - {plugin_file.name}")

    return True

def build():
    """Основна функція для збірки проєкту."""
    print("--- Початок збірки проєкту ---")

    print("1/5. Пошук шляхів до моделей та даних...")

    # --- ЗНАХОДИМО РЕСУРСИ PVPORCUPINE (НАДІЙНИЙ СПОСІБ) ---
    pvporcupine_path = get_package_path("pvporcupine")
    if not pvporcupine_path:
        print("Неможливо продовжити: пакет 'pvporcupine' не знайдено.")
        sys.exit(1)

    # Визначаємо шляхи до обох папок: lib та resources
    pv_lib_path = pvporcupine_path / "lib"
    pv_resources_path = pvporcupine_path / "resources"
    print(f"   > Знайдено pvporcupine 'lib': {pv_lib_path}")
    print(f"   > Знайдено pvporcupine 'resources': {pv_resources_path}")

    assets_path = ASSETS_DIR
    plugins_path = PLUGINS_DIR

    # --- ПЕРЕВІРКА НАЯВНОСТІ ФАЙЛІВ ПЕРЕД ЗБІРКОЮ ---
    if not pv_lib_path.exists() or not pv_resources_path.exists():
        print("[ПОМИЛКА] Критична помилка: папки 'lib' або 'resources' не знайдено всередині pvporcupine.")
        sys.exit(1)

    if not ICON_FILE.exists():
        print(f"[ПОМИЛКА] Критична помилка: Файл іконки не знайдено за шляхом: {ICON_FILE}")
        sys.exit(1)

    # --- transcriber.py тепер в root папці, не потрібно додавати окремо ---

    print("[OK] Шляхи успішно знайдено.")

    print("2/5. Формування команди PyInstaller...")
    command = [
        'pyinstaller',
        '--onefile',
        f'--name={EXE_NAME}',
        f'--icon={ICON_FILE}',
        # Додаємо обидві папки pvporcupine
        f'--add-data={pv_lib_path}{os.pathsep}pvporcupine/lib',
        f'--add-data={pv_resources_path}{os.pathsep}pvporcupine/resources',
        f'--add-data={assets_path}{os.pathsep}assets',
        f'--add-data={plugins_path}{os.pathsep}plugins',
        MAIN_SCRIPT
    ]
    if HIDE_CONSOLE:
        command.append('--noconsole')
        
    print(f"   > Команда: {' '.join(command)}")

    print("\n3/5. Запуск процесу збірки... Це може зайняти деякий час.")
    try:
        # ... (решта коду запуску та очищення залишається без змін) ...
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                   text=True, encoding='utf-8', errors='replace')
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        if process.returncode != 0:
             raise subprocess.CalledProcessError(process.returncode, command)
             
        print("[OK] Збірка успішно завершена.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"\n[ПОМИЛКА] ПОМИЛКА ПІД ЧАС ЗБІРКИ:")
        if isinstance(e, FileNotFoundError):
            print("   > Команда 'pyinstaller' не знайдена. Встановіть її: pip install pyinstaller")
        else:
            print(f"   > PyInstaller завершився з помилкою (код {e.returncode}).")
        return

    print("\n4/6. Копіювання C# додатку налаштувань...")
    copy_csharp_settings_app()

    print("\n5/6. Копіювання папки plugins...")
    copy_plugins_folder()

    print("\n6/6. Очищення тимчасових файлів...")
    try:
        shutil.rmtree('build', ignore_errors=True)
        os.remove(f'{EXE_NAME}.spec')
        print("[OK] Тимчасові файли видалено.")
    except OSError as e:
        print(f"[УВАГА] Не вдалося видалити тимчасові файли: {e}")

    print(f"\n--- Готово! ---")
    print(f"Основний додаток: dist/{EXE_NAME}.exe")
    print(f"Налаштування: dist/AlexaSettingsApp.exe")
    print(f"--- Не забудьте покласти файл 'config.json' в папку 'dist' ---")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--copy-csharp-only":
        # Тільки копіювання C# додатку без Python білду
        print("--- Копіювання тільки C# додатку ---")
        copy_csharp_settings_app()
    else:
        # Повний білд
        build()