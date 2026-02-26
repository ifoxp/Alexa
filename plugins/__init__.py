"""
Smart plugins package for AI-powered voice assistant.
Automatically dynamically loads all available plugins in the directory.
"""

import os
import pkgutil
import importlib
import inspect
from .base_plugin import SmartPlugin

# Список всіх доступних плагінів
AVAILABLE_PLUGINS = []

# Отримуємо шлях до поточної папки (де лежить цей __init__.py)
package_dir = os.path.dirname(__file__)

# Проходимося по всіх файлах .py у цій папці
for (_, module_name, ispkg) in pkgutil.iter_modules([package_dir]):
    # Пропускаємо базовий клас, щоб не імпортувати його як активний плагін
    if module_name == "base_plugin":
        continue

    try:
        # Динамічно імпортуємо модуль (аналог from .module_name import *)
        module = importlib.import_module(f".{module_name}", package=__name__)

        # Скануємо все, що є всередині модуля
        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)
            
            # Перевіряємо, чи це КЛАС і чи успадковується він від SmartPlugin
            if inspect.isclass(attribute) and issubclass(attribute, SmartPlugin):
                # Відсікаємо сам базовий клас, якщо він випадково імпортувався
                if attribute is not SmartPlugin:
                    # Уникаємо дублікатів
                    if attribute not in AVAILABLE_PLUGINS:
                        AVAILABLE_PLUGINS.append(attribute)
                        
    except Exception as e:
        print(f"[PLUGIN LOADER] Помилка завантаження плагіна {module_name}: {e}")

__all__ = ['SmartPlugin', 'AVAILABLE_PLUGINS']