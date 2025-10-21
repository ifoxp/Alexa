# settings.py
import pyaudio
import os

# !!! ВАЖЛИВО: Вставте сюди ваш AccessKey з сайту Picovoice Console !!!
PICOVOICE_ACCESS_KEY = "CeVnRNJScYlhq2hbOKtZCrZI7eUxWZKRIi8AaUQ2AHN+j+XF7Nt4nQ=="
# --- Аудіо Налаштування ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 512

# --- Налаштування Wake Word (Porcupine) ---
WAKE_WORD_MODELS = ["alexa", "jarvis"]
ACTIVATION_THRESHOLD = 0.5
DETECTION_COOLDOWN = 1.0

# --- Налаштування Транскрипції (SpeechRecognition) ---
DEFAULT_LANGUAGE = "uk-UA"

# --- Налаштування Обробки Команд ---
COMMAND_SESSION_TIMEOUT = 15     # Загальний час сесії слухання команд (секунди)
CONTINUOUS_LISTEN_SECONDS = 5    # Скільки секунд тиші чекати після останньої команди
SILENCE_DETECT_SECONDS = 1.5     # Скільки секунд тиші вважати кінцем фрази