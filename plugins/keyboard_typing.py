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
        return "Автоматичне друкування тексту на клавіатурі користувача. АБСОЛЮТНИЙ ПРІОРИТЕТ: Якщо репліка починається зі слів 'напиши', 'надрукуй', 'введи', 'набери' — це ЗАВЖДИ цей плагін, незалежно від того, що саме треба написати (фільм, пісню чи випадковий текст)"
    
    @property
    def commands(self) -> Dict[str, str]:
        # Головна фішка тут — інструкція для ШІ з очищення тексту
        return {
            "type_text": "надрукувати текст. Значення — рядок тексту. ВАЖЛИВО: очисти текст від слів-команд ('напиши', 'ну', 'типу', 'будь ласка'). Приклад: Користувач каже 'напиши ну дивитися Валлі українською' -> {'type_text': 'Дивитися Валлі українською'}."
        }

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        try:
            print(f"\n=== KEYBOARD API DEBUG ===")
            print(f"[1] Command: {command_name} | Args: {kwargs}")

            command_value = kwargs.get("value")
            if command_value is None and kwargs:
                command_value = list(kwargs.values())[0]

            if command_name == "type_text":
                text_to_type = str(command_value)
                
                if not text_to_type:
                    return {"success": False, "result": None, "message": "Немає тексту для введення."}

                # Невеличка пауза (0.2 сек), щоб переконатися, що курсор точно в полі після того, як ти закінчив говорити
                time.sleep(0.2) 

                # Функція write сама розпізнає розкладку і друкує Unicode
                keyboard.write(text_to_type, delay=0.01)

                return {"success": True, "result": None, "message": "Текст успішно надруковано."}

            return {"success": False, "result": None, "message": f"Невідома команда плагіна: {command_name}"}

        except Exception as e:
            self.log_error(f"Keyboard Typing Error: {e}")
            return {"success": False, "result": None, "message": f"Помилка клавіатури: {str(e)}"}