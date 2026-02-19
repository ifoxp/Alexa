import pyaudio
import config_manager

print("Ініціалізація settings.py...")

# Завантажуємо конфігурацію через config_manager
try:
    config = config_manager.load_config()
    print("OK: Налаштування завантажено")
except Exception as e:
    print(f"ПОМИЛКА: Критична помилка в settings.py: {e}")
    config = {
        'commandSessionTimeout': 15,
        'continuousListenSeconds': 7,
        'silenceDetectSeconds': 1.5
    }

# --- Налаштування Обробки Команд (з config.json) ---
COMMAND_SESSION_TIMEOUT = config.get('commandSessionTimeout', 15)
CONTINUOUS_LISTEN_SECONDS = config.get('continuousListenSeconds', 7)
# Збільшуємо час детекції тиші для кращого захоплення кінця речень
SILENCE_DETECT_SECONDS = config.get('silenceDetectSeconds', 2.0)  # Було 1.5
# Збільшуємо таймаут тиші для async операцій
SILENCE_TIMEOUT = config.get('silenceTimeout', 6.0)  # Було 5.0

print(f"COMMAND_SESSION_TIMEOUT = {COMMAND_SESSION_TIMEOUT}")
print(f"CONTINUOUS_LISTEN_SECONDS = {CONTINUOUS_LISTEN_SECONDS}")
print(f"SILENCE_DETECT_SECONDS = {SILENCE_DETECT_SECONDS}")
print(f"SILENCE_TIMEOUT = {SILENCE_TIMEOUT}")

# --- Аудіо Налаштування (незмінні) ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 512