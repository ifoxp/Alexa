# settings.py
import pyaudio

# --- Налаштування Обробки Команд (залишаються тут) ---
COMMAND_SESSION_TIMEOUT = 15
CONTINUOUS_LISTEN_SECONDS = 5
SILENCE_DETECT_SECONDS = 1.5

# --- Аудіо Налаштування (незмінні) ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 512