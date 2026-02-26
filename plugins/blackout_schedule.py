import json
import os
from datetime import datetime
from typing import Dict, Any
from .base_plugin import SmartPlugin

class BlackoutSchedulePlugin(SmartPlugin):
    """Плагін для перевірки графіка відключень світла (все що пов'язано з включенням відключенням і графіком світла тут)."""

    @property
    def name(self) -> str:
        return "blackout_schedule"

    @property
    def description(self) -> str:
        return "Перевіряє графік відключень світла. Використовуй для питань: 'Коли увімкнуть світло?', 'Коли вимкнуть?', або 'Який графік відключень на сьогодні?'."

    @property
    def commands(self) -> Dict[str, str]:
        return {
            "when_light_on": "Дізнатися, коли найближчим часом з'явиться світло (якщо зараз його немає)",
            "when_light_off": "Дізнатися, коли найближчим часом вимкнуть світло (якщо зараз воно є)",
            "get_schedule": "Прочитати графік відключень до кінця доби (від поточної години)"
        }

    def _read_schedule(self) -> list:
        """Читає години відключень з локального файлу."""
        # Використовуємо 'r' перед рядком, щоб зворотні слеші у шляху Windows читалися правильно
        file_path = r"E:\Programs\EcoFlowStats\schedule.json"
        
        if not os.path.exists(file_path):
            self.log_error(f"Файл не знайдено: {file_path}")
            return None
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Повертаємо список годин відключень, наприклад: [4, 5, 8, 9, 10, 11...]
                return data.get("outages", [])
        except Exception as e:
            self.log_error("Помилка читання JSON файлу графіка", error=str(e))
            return None

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        """Виконує команду плагіна."""
        print(f"\n=== BLACKOUT SCHEDULE DEBUG ===")
        print(f"[1] Received command: {command_name}")

        outages = self._read_schedule()
        
        if outages is None:
            return {
                "success": False,
                "result": None,
                "message": "Файл графіка не знайдено або він пошкоджений.",
                "speak_text": "Вибачте, сер, але я не зміг отримати доступ до файлу з графіком відключень."
            }
            
        # Отримуємо поточну годину (0-23)
        current_hour = datetime.now().hour
        
        try:
            if command_name == "when_light_on":
                return self._when_light_on(current_hour, outages)
                
            elif command_name == "when_light_off":
                return self._when_light_off(current_hour, outages)
                
            elif command_name == "get_schedule":
                return self._get_schedule(current_hour, outages)
                
            else:
                return {"success": False, "result": None, "message": f"Невідома команда: {command_name}"}

        except Exception as e:
            self.log_error(f"Помилка виконання {command_name}", error=str(e))
            return {"success": False, "result": None, "message": f"Сталася помилка: {str(e)}"}

    def _when_light_on(self, current_hour: int, outages: list) -> Dict[str, Any]:
        """Шукає найближчу годину, коли світло з'явиться."""
        if current_hour not in outages:
            text = "Світло зараз є, сер. Можете не хвилюватися."
            return {"success": True, "result": {"status": "on"}, "message": "Світло вже є", "speak_text": text}
        
        # Шукаємо першу годину до кінця доби, якої НЕМАЄ в списку відключень
        for h in range(current_hour + 1, 24):
            if h not in outages:
                text = f"Світло увімкнуть о {h}, сер."
                return {"success": True, "result": {"next_on": h}, "message": text, "speak_text": text}
                
        text = "На жаль, світла не буде до кінця доби, сер."
        return {"success": True, "result": {"next_on": None}, "message": text, "speak_text": text}

    def _when_light_off(self, current_hour: int, outages: list) -> Dict[str, Any]:
        """Шукає найближчу годину, коли світло зникне."""
        if current_hour in outages:
            text = "Світла зараз і так немає, сер."
            return {"success": True, "result": {"status": "off"}, "message": "Світла вже немає", "speak_text": text}
            
        # Шукаємо першу годину до кінця доби, яка Є в списку відключень
        for h in range(current_hour + 1, 24):
            if h in outages:
                text = f"Світло вимкнуть о {h}, сер."
                return {"success": True, "result": {"next_off": h}, "message": text, "speak_text": text}
                
        text = "Сьогодні відключень більше не планується, сер."
        return {"success": True, "result": {"next_off": None}, "message": text, "speak_text": text}

    def _get_schedule(self, current_hour: int, outages: list) -> Dict[str, Any]:
        """Формує людський графік від поточної години до кінця доби (згруповано)."""
        if current_hour >= 23:
            text = "Вже майже кінець доби, сер."
            return {"success": True, "result": {"schedule": []}, "message": text, "speak_text": text}

        schedule_parts = []
        
        # Визначаємо поточний стан: True якщо світло Є, False якщо НЕМАЄ
        current_state = current_hour not in outages 
        start_hour = current_hour

        # Проходимося по годинах включно до 24, щоб закрити останній блок
        for h in range(current_hour + 1, 25):
            # Визначаємо стан для години h
            is_on = h not in outages if h < 24 else not current_state # 24 - примусова зміна для закриття блоку
            
            # Якщо стан змінився (світло з'явилося або зникло), записуємо блок
            if is_on != current_state:
                state_text = "світло є" if current_state else "світла немає"
                # Форматуємо як "з 10:00 до 12:00 світла немає"
                # Використовуємо ... для невеличких пауз під час озвучки
                schedule_parts.append(f"з {start_hour} до {h} {state_text}...")
                
                start_hour = h
                current_state = is_on

        # Збираємо все в один текст
        if not schedule_parts:
            final_text = "Графік відключень порожній, сер."
        else:
            final_text = f"Графік до кінця дня. {'; '.join(schedule_parts)}. Ось так, сер."

        return {
            "success": True,
            "result": {"raw_schedule": schedule_parts},
            "message": "Озвучую графік",
            "speak_text": final_text
        }