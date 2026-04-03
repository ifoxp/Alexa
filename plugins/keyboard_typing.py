import keyboard
import time
from typing import Dict, Any
from .base_plugin import SmartPlugin

class KeyboardTypingPlugin(SmartPlugin):
    """Плагін для імітації натискань клавіатури та автоматичного введення тексту."""

    def __init__(self):
        super().__init__()

    @property
    def name(self) -> str:
        return "keyboard_typing"

    @property
    def description(self) -> str:
        return "Друкує текст на клавіатурі. Якщо репліка ПОЧИНАЄТЬСЯ зі слів 'напиши', 'надрукуй', 'введи', 'набери' — ВСЕ що йде після цього слова є текстом для введення, а НЕ окремою командою. Приклад: 'напиши Привет как дела пошли гулять' → надрукувати 'Привет как дела пошли гулять'. Зміст тексту не аналізується."
    
    @property
    def commands(self) -> Dict[str, str]:
        # Головна фішка тут — інструкція для ШІ з очищення тексту
        return {
            "type_text": "надрукувати текст. Значення — рядок тексту. ВАЖЛИВО: очисти текст від слів-команд ('напиши', 'ну', 'типу', 'будь ласка'). Приклад: Користувач каже 'напиши ну дивитися Валлі українською' -> {'type_text': 'Дивитися Валлі українською'}."
        }

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        try:
            print(f"[KEYBOARD] execute: command={command_name}, kwargs={kwargs}")

            command_value = kwargs.get("value")
            if command_value is None and kwargs:
                command_value = list(kwargs.values())[0]

            if command_name == "type_text":
                text_to_type = str(command_value)

                if not text_to_type:
                    print(f"[KEYBOARD] no text provided")
                    return {"success": False, "result": None, "message": "Немає тексту для введення."}

                print(f"[KEYBOARD] typing ({len(text_to_type)} chars): '{text_to_type}'")
                time.sleep(0.2)
                keyboard.write(text_to_type, delay=0.01)
                print(f"[KEYBOARD] done")
                return {"success": True, "result": None, "message": "Текст успішно надруковано."}

            print(f"[KEYBOARD] unknown command: {command_name}")
            return {"success": False, "result": None, "message": f"Невідома команда плагіна: {command_name}"}

        except Exception as e:
            print(f"[KEYBOARD] error: {e}")
            return {"success": False, "result": None, "message": f"Помилка клавіатури: {str(e)}"}