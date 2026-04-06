# config_manager.py
import json
import os
import sys

CONFIG_FILE = "config.json"

def load_config():
    """
    Завантажує конфігурацію, гарантуючи наявність всіх ключів
    та перевіряючи AccessKey.
    """
    # Спочатку створюємо конфіг з дефолтними значеннями
    config = {
        "picovoiceAccessKey": "",
        "wakeWordStandard": "porcupine",
        "sensitivity": 0.5,
        "languages": ["uk-UA", "ru-RU", "en-US"],
        "microphoneDevice": ""
    }

    if not os.path.exists(CONFIG_FILE):
        print(f"⚠️ Файл {CONFIG_FILE} не знайдено. Буде створено новий.")
        # Створюємо новий файл з дефолтними значеннями, але без ключа
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        raise ValueError(f"Будь ласка, відкрийте {CONFIG_FILE} і вставте ваш picovoiceAccessKey.")

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            # Оновлюємо дефолтні значення тими, що є у файлі
            config.update(user_config)
    except Exception as e:
        raise ValueError(f"Помилка читання {CONFIG_FILE}: {e}")

    # Критична перевірка наявності ключа
    if not config.get("picovoiceAccessKey") or "ПАСТА_СЮДИ" in config.get("picovoiceAccessKey", ""):
        raise ValueError(f"AccessKey відсутній або не встановлений у {CONFIG_FILE}.")

    # Зберігаємо оновлений конфіг (якщо у файлі бракувало якихось полів)
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    except PermissionError:
        print(f"⚠️ Не вдалося оновити {CONFIG_FILE} (немає прав на запис). Продовжуємо з поточними налаштуваннями.")

    return config