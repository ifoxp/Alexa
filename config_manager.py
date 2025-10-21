# config_manager.py
import json
import os

CONFIG_FILE = "config.json"
DEFAULT_CONFIG = {
    "picovoiceAccessKey": "",
    "wakeWordStandard": "porcupine",
    "sensitivity": 0.5,
    "language": "uk-UA"
}

def load_config():
    """Завантажує конфігурацію з config.json."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # Перевіряємо, чи є ключ
                if not config.get("picovoiceAccessKey") or "ПАСТА_СЮДИ" in config.get("picovoiceAccessKey", ""):
                     print("ПОПЕРЕДЖЕННЯ: AccessKey не знайдено або не встановлено в config.json.")
                     # Можна повернути помилку або дефолтні значення
                     # return DEFAULT_CONFIG # Або викликати sys.exit()
                     raise ValueError("AccessKey відсутній у config.json")
                return config
        except ValueError as ve: # Ловимо нашу помилку
             print(f"Критична помилка: {ve}")
             # Тут можна додати логіку для виходу з програми або повідомлення користувачу
             # Наприклад:
             # import sys
             # sys.exit(1)
             raise # Передаємо помилку далі, щоб програма зупинилася
        except Exception as e:
            print(f"Помилка завантаження config.json: {e}. Використовуються значення за замовчуванням (не рекомендовано).")
            return DEFAULT_CONFIG # Або можна викликати raise, щоб зупинити програму
    else:
        print(f"Критична помилка: Файл {CONFIG_FILE} не знайдено.")
        raise FileNotFoundError(f"Файл {CONFIG_FILE} не знайдено.") # Зупиняємо програму