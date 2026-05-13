# config_manager.py
import json
import os
import sys

def _get_config_path() -> str:
    """Повертає абсолютний шлях до config.json поряд з exe або скриптом."""
    if getattr(sys, 'frozen', False):
        # exe-режим: поряд з Alexa.exe
        base = os.path.dirname(sys.executable)
    else:
        # dev-режим: поряд з config_manager.py
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "config.json")

CONFIG_FILE = _get_config_path()

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
            content = f.read().strip()
        if not content:
            print(f"⚠️ {CONFIG_FILE} порожній — буде перезаписаний дефолтними значеннями.")
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            raise ValueError(f"Будь ласка, відкрийте {CONFIG_FILE} і вставте ваш picovoiceAccessKey.")
        user_config = json.loads(content)
        config.update(user_config)
    except ValueError:
        raise
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