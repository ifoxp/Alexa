import os
import sys
import shutil
import subprocess

# --- НАЛАШТУВАННЯ БІЛДУ ---
EXE_NAME = "Alexa"
MAIN_SCRIPT = "main.py"
HIDE_CONSOLE = False # False, щоб бачити консоль
ASSETS_DIR = "assets" # Назва вашої папки з ресурсами

def find_pvporcupine_resources_path():
    try:
        import pvporcupine
        package_path = os.path.dirname(pvporcupine.__file__)
        resources_path = os.path.join(package_path, "lib")
        if os.path.exists(resources_path):
            print(f"   > Знайдено ресурси pvporcupine у: {resources_path}")
            return resources_path
        return None
    except Exception as e:
        print(f"❌ Помилка під час пошуку ресурсів pvporcupine: {e}")
        return None

def build():
    print("--- Початок збірки проєкту ---")

    print("1/4. 🔍 Пошук шляхів до моделей та даних...")
    pv_resources_path = find_pvporcupine_resources_path()
    stt_path = "stt"
    assets_path = ASSETS_DIR

    if not pv_resources_path: sys.exit(1)
    if not os.path.exists(stt_path):
        print(f"❌ Помилка: Папка '{stt_path}' не знайдена.")
        sys.exit(1)
    if not os.path.exists(assets_path):
        print(f"⚠️ Попередження: Папка '{assets_path}' не знайдена, звуки не будуть додані.")

    print("✅ Шляхи успішно знайдено.")

    print("2/4. 🛠️  Формування команди PyInstaller...")
    command = [
        'pyinstaller',
        '--onefile',
        f'--name={EXE_NAME}',
        f'--add-data={pv_resources_path}{os.pathsep}pvporcupine/lib',
        f'--add-data={stt_path}{os.pathsep}{stt_path}',
        f'--add-data={assets_path}{os.pathsep}{assets_path}', # <-- ДОДАНО ПАПКУ ASSETS
        MAIN_SCRIPT
    ]
    if HIDE_CONSOLE:
        command.append('--noconsole')
    print(f"   > Команда: {' '.join(command)}")

    print("\n3/4. 🚀 Запуск процесу збірки...")
    try:
        with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace') as process:
            for line in process.stdout:
                print(line, end='')
        if process.returncode != 0:
             raise subprocess.CalledProcessError(process.returncode, command)
        print("✅ Збірка успішно завершена.")
    except Exception as e:
        print(f"\n❌ ПОМИЛКА ПІД ЧАС ЗБІРКИ: {e}")
        return

    print("\n4/4. 🧹 Очищення тимчасових файлів...")
    try:
        shutil.rmtree('build', ignore_errors=True)
        os.remove(f'{EXE_NAME}.spec')
        print("✅ Тимчасові файли видалено.")
    except OSError as e:
        print(f"⚠️ Не вдалося видалити тимчасові файли: {e}")

    print(f"\n--- 🎉 Готово! Ваш файл '{EXE_NAME}.exe' знаходиться в папці 'dist' ---")

if __name__ == "__main__":
    build()