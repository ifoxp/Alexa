import os
from datetime import datetime
import asyncio

class CommandLogger:
    def __init__(self, log_file="commands_log.txt"):
        self.log_file = log_file
        self.lock = asyncio.Lock()

    async def log_command(self, user_command: str, stage1_response: str = "", stage2_response: str = ""):
        """Логує команду користувача та відповіді GPT етапу 1 і 2"""
        async with self.lock:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                log_entry = f"""
========================================
Час: {timestamp}
Команда користувача: {user_command}
GPT Етап 1 (вибір плагінів): {stage1_response}
GPT Етап 2 (команди + відповідь): {stage2_response}
========================================

"""

                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(log_entry)

                print(f"Команда залогована в {self.log_file}")

            except Exception as e:
                print(f"Помилка логування: {e}")

    def clear_log(self):
        """Очищає лог файл"""
        try:
            if os.path.exists(self.log_file):
                os.remove(self.log_file)
                print(f"Лог файл {self.log_file} очищено")
            else:
                print("Лог файл не існує")
        except Exception as e:
            print(f"Помилка очищення логу: {e}")

    def get_log_size(self):
        """Повертає розмір лог файлу"""
        try:
            if os.path.exists(self.log_file):
                size = os.path.getsize(self.log_file)
                return f"Розмір лог файлу: {size} байт"
            else:
                return "Лог файл не існує"
        except Exception as e:
            return f"Помилка перевірки розміру: {e}"

# Глобальний екземпляр логера
command_logger = CommandLogger()