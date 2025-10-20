import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_requirements():
    """Встановлення необхідних пакетів"""
    requirements = [
        "pyaudio",
        "numpy",
        "openwakeword",
        "pyinstaller"
    ]

    print("Встановлення залежностей...")
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"[OK] {package} встановлено")
        except subprocess.CalledProcessError:
            print(f"[ERROR] Помилка встановлення {package}")
            return False
    return True

def create_spec_file():
    """Створення spec файлу для PyInstaller"""
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'openwakeword',
        'openwakeword.model',
        'wake_word',
        'pyaudio',
        'numpy'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AlexaWakeWord',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''

    with open('alexa_wakeword.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("[OK] Spec файл створено")

def build_executable():
    """Створення виконуваного файлу"""
    print("Початок збирання exe файлу...")

    try:
        # Використання spec файлу для збирання
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "alexa_wakeword.spec"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("[OK] Exe файл успішно створено!")
            print("Знайти можна в папці: dist/AlexaWakeWord.exe")
            return True
        else:
            print("[ERROR] Помилка під час збирання:")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"[ERROR] Помилка: {e}")
        return False

def cleanup():
    """Очищення тимчасових файлів"""
    print("Очищення тимчасових файлів...")

    dirs_to_remove = ['build', '__pycache__']
    files_to_remove = ['alexa_wakeword.spec']

    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Видалено {dir_name}")

    for file_name in files_to_remove:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"Видалено {file_name}")

def main():
    """Основна функція збирання"""
    print("Початок збирання Alexa Wake Word в exe...")
    print("=" * 50)

    # Перевірка наявності основних файлів
    required_files = ['main.py', 'wake_word.py']
    for file_name in required_files:
        if not os.path.exists(file_name):
            print(f"[ERROR] Файл {file_name} не знайдено!")
            return False

    # Встановлення залежностей
    if not install_requirements():
        print("[ERROR] Не вдалося встановити залежності")
        return False

    # Створення spec файлу
    create_spec_file()

    # Збирання exe
    if build_executable():
        print("\n[SUCCESS] Збирання завершено успішно!")
        print("Інструкції:")
        print("   1. Запустіть dist/AlexaWakeWord.exe")
        print("   2. Скажіть 'Alexa' в мікрофон")
        print("   3. Програма покаже повідомлення про розпізнавання")

        # Опційне очищення
        user_input = input("\nВидалити тимчасові файли? (y/n): ")
        if user_input.lower() in ['y', 'yes', 'так']:
            cleanup()

        return True
    else:
        print("[ERROR] Збирання не вдалося")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)