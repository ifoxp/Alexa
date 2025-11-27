import pyaudio
import os
import sys
import json

# Завантаження конфігурації з config.json
def load_config():
    try:
        print("🔧 Завантаження конфігурації...")

        # Визначаємо правильний шлях до config.json
        if hasattr(sys, '_MEIPASS'):
            # Якщо запущено через PyInstaller
            config_path = os.path.join(os.path.dirname(sys.executable), 'config.json')
            print(f"   PyInstaller режим: {config_path}")
        else:
            # Якщо запущено як звичайний Python скрипт
            config_path = os.path.join(os.path.dirname(__file__), 'config.json')
            print(f"   Звичайний режим: {config_path}")

        if not os.path.exists(config_path):
            print(f"❌ Файл config.json не знайдено: {config_path}")
            # Повертаємо значення за замовчуванням
            return {
                'commandSessionTimeout': 15,
                'continuousListenSeconds': 7,
                'silenceDetectSeconds': 1.5
            }

        print(f"✅ Читаю config.json з: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            print("✅ Конфігурацію завантажено успішно")
            return config_data

    except Exception as e:
        print(f"❌ Помилка завантаження config.json: {e}")
        # Повертаємо значення за замовчуванням
        return {
            'commandSessionTimeout': 15,
            'continuousListenSeconds': 7,
            'silenceDetectSeconds': 1.5
        }

print("📋 Ініціалізація settings.py...")

# Завантажуємо конфігурацію з обробкою помилок
try:
    config = load_config()
    print("✅ Налаштування завантажено")
except Exception as e:
    print(f"❌ Критична помилка в settings.py: {e}")
    config = {
        'commandSessionTimeout': 15,
        'continuousListenSeconds': 7,
        'silenceDetectSeconds': 1.5
    }

# --- Налаштування Обробки Команд (з config.json) ---
COMMAND_SESSION_TIMEOUT = config.get('commandSessionTimeout', 15)
CONTINUOUS_LISTEN_SECONDS = config.get('continuousListenSeconds', 7)
SILENCE_DETECT_SECONDS = config.get('silenceDetectSeconds', 1.5)

print(f"⚙️ COMMAND_SESSION_TIMEOUT = {COMMAND_SESSION_TIMEOUT}")
print(f"⚙️ CONTINUOUS_LISTEN_SECONDS = {CONTINUOUS_LISTEN_SECONDS}")
print(f"⚙️ SILENCE_DETECT_SECONDS = {SILENCE_DETECT_SECONDS}")

# --- Аудіо Налаштування (незмінні) ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 512