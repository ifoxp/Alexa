# logger_config.py
import logging
import sys
import os
from datetime import datetime
from pathlib import Path

def setup_logger(name='alexa_assistant', level=logging.WARNING):
    """Налаштовує structured logging для асистента."""

    # Створюємо папку для логів поруч із виконуваним файлом (або скриптом)
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).parent
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(exist_ok=True)

    # Формат для логів
    log_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s | %(filename)s:%(lineno)d',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Консольний handler (замість print)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(log_format)

    # Файловий handler для всіх логів
    log_file = logs_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)  # Тільки INFO і вище
    file_handler.setFormatter(log_format)

    # Окремий файл для помилок
    error_file = logs_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.FileHandler(error_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(log_format)

    # Налаштовуємо основний логер
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Видаляємо старі handlers якщо є
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Додаємо нові handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)

    # Запобігаємо дублюванню логів
    logger.propagate = False

    return logger

# Глобальний логер для всього проекту
logger = setup_logger()

def get_logger(module_name):
    """Отримує логер для конкретного модуля."""
    return logging.getLogger(f'alexa_assistant.{module_name}')