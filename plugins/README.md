# 🔌 Alexa Assistant Plugin System

## Що таке плагіни?

Плагіни - це модулі, які розширюють можливості Alexa Assistant. Кожен плагін може обробляти певні типи команд (запуск програм, пошук в браузері, системні функції).

## 📁 Структура плагіна

Кожен плагін має бути файлом `.py` в папці `plugins/` та наслідувати клас `SmartPlugin`:

```python
# my_plugin.py
from typing import Dict, Any
from .base_plugin import SmartPlugin

class MyPlugin(SmartPlugin):
    @property
    def name(self) -> str:
        return "my_plugin"  # Унікальна назва плагіна

    @property
    def description(self) -> str:
        return "Опис того, що робить плагін"

    @property
    def commands(self) -> Dict[str, str]:
        return {
            "my_command": "опис команди (параметр)"
        }

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        if command_name == "my_command":
            value = kwargs.get("value", "")
            # Ваша логіка тут
            return {
                "success": True,
                "result": {"data": "result"},
                "message": "Команда виконана успішно"
            }
```

## 🛠️ Можливості плагінів

### 1. Логування
```python
# Успішне виконання
self.log_info("Повідомлення про успіх")

# Помилки
self.log_error("Опис помилки", error="деталі помилки")
```

### 2. Отримання параметрів
```python
# ШІ передає параметри як 'value'
value = kwargs.get("value", "default")

# Можна також підтримувати альтернативні назви
query = kwargs.get("value") or kwargs.get("query", "")
```

### 3. Повернення результатів
```python
# Успішне виконання
return {
    "success": True,
    "result": {"key": "value"},
    "message": "Що показати користувачу"
}

# Помилка
return {
    "success": False,
    "result": None,
    "message": "Що пішло не так"
}
```

## 📚 Приклади плагінів

### Простий плагін для розрахунків
```python
import math
from typing import Dict, Any
from .base_plugin import SmartPlugin

class CalculatorPlugin(SmartPlugin):
    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Математичні розрахунки: додавання, множення, корені"

    @property
    def commands(self) -> Dict[str, str]:
        return {
            "add": "додати числа (число1 плюс число2)",
            "multiply": "помножити числа (число1 на число2)",
            "sqrt": "квадратний корінь (число)"
        }

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        try:
            if command_name == "add":
                # Користувач: "додай 5 плюс 3"
                text = kwargs.get("value", "")
                numbers = [float(x) for x in text.split() if x.replace('.','').isdigit()]
                result = sum(numbers)

                return {
                    "success": True,
                    "result": {"numbers": numbers, "sum": result},
                    "message": f"Сума: {result}"
                }

        except Exception as e:
            self.log_error(f"Calculator error in {command_name}", error=str(e))
            return {
                "success": False,
                "result": None,
                "message": f"Помилка розрахунку: {str(e)}"
            }
```

### Плагін для роботи з файлами
```python
import os
from typing import Dict, Any
from .base_plugin import SmartPlugin

class FileManagerPlugin(SmartPlugin):
    @property
    def name(self) -> str:
        return "file_manager"

    @property
    def description(self) -> str:
        return "Управління файлами: створення папок, пошук файлів"

    @property
    def commands(self) -> Dict[str, str]:
        return {
            "create_folder": "створити папку (назва папки)",
            "find_file": "знайти файл (назва файла)"
        }

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        try:
            if command_name == "create_folder":
                folder_name = kwargs.get("value", "")
                desktop = os.path.join(os.path.expanduser("~"), "Desktop")
                folder_path = os.path.join(desktop, folder_name)

                os.makedirs(folder_path, exist_ok=True)

                return {
                    "success": True,
                    "result": {"path": folder_path},
                    "message": f"Папку '{folder_name}' створено на робочому столі"
                }

        except Exception as e:
            self.log_error(f"File manager error", error=str(e))
            return {
                "success": False,
                "result": None,
                "message": f"Помилка: {str(e)}"
            }
```

## 🔄 Автоматичне завантаження

Плагіни завантажуються автоматично! Просто:

1. ✅ Створіть файл `.py` в папці `plugins/`
2. ✅ Наслідуйте від `SmartPlugin`
3. ✅ Перезапустіть Alexa Assistant

**Не потрібно редагувати `__init__.py`!**

## 🎯 Поради по розробці

### 1. Назви команд
- Використовуйте зрозумілі назви: `send_email`, `play_music`
- Описи команд мають бути на українській: `"відправити email (адреса)"`

### 2. Обробка параметрів
- ШІ передає параметри як `value`
- Підтримуйте альтернативні назви для сумісності
- Перевіряйте наявність обов'язкових параметрів

### 3. Обробка помилок
- Завжди використовуйте `try/except`
- Логуйте помилки через `self.log_error()`
- Повертайте зрозумілі повідомлення користувачу

### 4. Асінхронність
- Всі методи мають бути `async`
- Для довгих операцій використовуйте `await`
- Для синхронних операцій просто додайте `async`

## 🚀 Тестування плагіна

1. Додайте плагін в папку `plugins/`
2. Перезапустіть Alexa Assistant
3. Скажіть команду що має обробити ваш плагін
4. Перевірте логи для помилок

## ❓ Поширені проблеми

**Плагін не завантажується:**
- Перевірте синтаксис Python
- Переконайтеся що наслідується від `SmartPlugin`
- Перевірте чи всі методи реалізовані

**Команда не виконується:**
- Перевірте назву команди в `commands`
- Переконайтеся що `execute_command` обробляє цю команду
- Перевірте логи на помилки

**ШІ не розпізнає команду:**
- Зробіть опис команди більш зрозумілим
- Додайте синоніми в опис: `"грати музику або відтворити пісню"`