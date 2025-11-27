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
COMMANDS_DIR = "commands"

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
        print(f"❌ Помилка під час пошуку пакету {package_name}: {e}")
        return None

def build():
    """Основна функція для збірки проєкту."""
    print("--- Початок збірки проєкту ---")

    print("1/4. 🔍 Пошук шляхів до моделей та даних...")

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

    stt_path = "stt"
    assets_path = ASSETS_DIR
    commands_path = COMMANDS_DIR

    # --- ПЕРЕВІРКА НАЯВНОСТІ ФАЙЛІВ ПЕРЕД ЗБІРКОЮ ---
    if not pv_lib_path.exists() or not pv_resources_path.exists():
        print("❌ Критична помилка: папки 'lib' або 'resources' не знайдено всередині pvporcupine.")
        sys.exit(1)
        
    if not ICON_FILE.exists():
        print(f"❌ Критична помилка: Файл іконки не знайдено за шляхом: {ICON_FILE}")
        sys.exit(1)

    # ... (решта перевірок)

    print("✅ Шляхи успішно знайдено.")

    print("2/4. 🛠️  Формування команди PyInstaller...")
    command = [
        'pyinstaller',
        '--onefile',
        f'--name={EXE_NAME}',
        f'--icon={ICON_FILE}',
        # !!! ВИПРАВЛЕНО: Додаємо обидві папки pvporcupine !!!
        f'--add-data={pv_lib_path}{os.pathsep}pvporcupine/lib',
        f'--add-data={pv_resources_path}{os.pathsep}pvporcupine/resources',
        f'--add-data={stt_path}{os.pathsep}stt',
        f'--add-data={assets_path}{os.pathsep}assets',
        f'--add-data={commands_path}{os.pathsep}commands',
        MAIN_SCRIPT
    ]
    if HIDE_CONSOLE:
        command.append('--noconsole')
        
    print(f"   > Команда: {' '.join(command)}")

    print("\n3/4. 🚀 Запуск процесу збірки... Це може зайняти деякий час.")
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
             
        print("✅ Збірка успішно завершена.")
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"\n❌ ПОМИЛКА ПІД ЧАС ЗБІРКИ:")
        if isinstance(e, FileNotFoundError):
            print("   > Команда 'pyinstaller' не знайдена. Встановіть її: pip install pyinstaller")
        else:
            print(f"   > PyInstaller завершився з помилкою (код {e.returncode}).")
        return

    print("\n4/4. 🧹 Очищення тимчасових файлів...")
    try:
        shutil.rmtree('build', ignore_errors=True)
        os.remove(f'{EXE_NAME}.spec')
        print("✅ Тимчасові файли видалено.")
    except OSError as e:
        print(f"⚠️ Не вдалося видалити тимчасові файли: {e}")

    print(f"\n--- 🎉 Готово! Ваш файл '{EXE_NAME}.exe' знаходиться в папці 'dist' ---")
    print(f"--- Не забудьте покласти файл 'config.json' поруч з '{EXE_NAME}.exe' ---")


if __name__ == "__main__":
    build()