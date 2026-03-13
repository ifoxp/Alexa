import os
import subprocess
import screen_brightness_control as sbc
from typing import Dict, Any
from .base_plugin import SmartPlugin

class MonitorControlPlugin(SmartPlugin):
    """Плагін для керування моніторами: яскравість та живлення через DDC/CI."""

    def __init__(self):
        super().__init__()
        # Перевіряємо монітори при старті ядра
        try:
            self.monitors = sbc.list_monitors()
            print(f"[MONITOR PLUGIN] Ініціалізація. Знайдено моніторів: {len(self.monitors)}")
            for i, name in enumerate(self.monitors):
                print(f"  -> Індекс [{i}]: {name}")
        except Exception as e:
            self.log_error(f"Failed to list monitors on init: {e}")
            self.monitors = []

    @property
    def name(self) -> str:
        return "monitor_control"

    @property
    def description(self) -> str:
        return "Керування моніторами та дисплеями: зміна яскравості конкретного монітора, вимкнення або увімкнення екранів."
    
    @property
    def commands(self) -> Dict[str, str]:
        # Few-Shot приклади гарантують, що ШІ видасть правильний формат навіть для кількох моніторів
        return {
            "set_brightness": "встановити яскравість. Значення — масив [номер, відсоток]. Якщо моніторів КІЛЬКА з РІЗНОЮ яскравістю, передавай масив масивів. Приклади: {'set_brightness': [2, 30]} (один монітор), АБО {'set_brightness': [[1, 55], [2, 30]]} (кілька моніторів одночасно), АБО {'set_brightness': ['all', 50]} (всі однаково).",
            "turn_off_monitor": "вимкнути монітор. Значення — номер монітора. Приклад: {'turn_off_monitor': 2}",
            "turn_on_monitor": "увімкнути монітор. Значення — номер монітора. Приклад: {'turn_on_monitor': 1}"
        }

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        try:
            print(f"\n=== MONITOR API DEBUG ===")
            print(f"[1] Command: {command_name} | Args: {kwargs}")

            # Отримуємо значення, яке згенерував ШІ (зазвичай лежить у ключі value)
            command_value = kwargs.get("value")
            if command_value is None and kwargs:
                command_value = list(kwargs.values())[0]

            available_monitors = sbc.list_monitors()
            if not available_monitors:
                return {"success": False, "result": None, "message": "Система не бачить жодного підключеного монітора."}

            # ==========================================
            # КОМАНДА: ЗМІНА ЯСКРАВОСТІ
            # ==========================================
            if command_name == "set_brightness":
                if not isinstance(command_value, list):
                    return {"success": False, "result": None, "message": "Неправильний формат параметрів. Очікувався масив."}

                # СЦЕНАРІЙ 1: Масив масивів (кілька моніторів з різною яскравістю, напр. [[1, 55], [2, 30]])
                if len(command_value) > 0 and isinstance(command_value[0], list):
                    success_msgs = []
                    for item in command_value:
                        if len(item) >= 2:
                            mon_id = item[0]
                            lvl = int(item[1])
                            disp_idx = int(mon_id) - 1
                            
                            # Захист від виходу за межі масиву
                            if disp_idx < 0 or disp_idx >= len(available_monitors):
                                continue

                            try:
                                sbc.set_brightness(lvl, display=disp_idx, method='vcp')
                                success_msgs.append(f"М{mon_id}: {lvl}%")
                            except Exception as e:
                                print(f"[MONITOR API] VCP помилка для [{disp_idx}]: {e}")
                                try:
                                    sbc.set_brightness(lvl, display=disp_idx)
                                    success_msgs.append(f"М{mon_id}: {lvl}% (резерв)")
                                except Exception:
                                    pass
                    
                    return {"success": True, "result": None, "message": f"Оновлено яскравість: {', '.join(success_msgs)}"}

                # СЦЕНАРІЙ 2: Одинарний масив (один монітор або всі, напр. [1, 55] або ["all", 50])
                elif len(command_value) >= 2:
                    monitor_id = command_value[0]
                    level = int(command_value[1])

                    # Якщо запит "для всіх"
                    if str(monitor_id).lower() == "all":
                        for i in range(len(available_monitors)):
                            try:
                                sbc.set_brightness(level, display=i, method='vcp')
                            except Exception as e:
                                print(f"[MONITOR API] VCP помилка для [{i}], фолбек на стандарт: {e}")
                                sbc.set_brightness(level, display=i)
                        return {"success": True, "result": None, "message": f"Яскравість всіх дисплеїв встановлено на {level} відсотків"}
                    
                    # Якщо для одного конкретного монітора
                    else:
                        display_index = int(monitor_id) - 1 

                        if display_index < 0 or display_index >= len(available_monitors):
                             return {"success": False, "result": None, "message": f"Монітор з номером {monitor_id} не знайдено."}

                        try:
                            sbc.set_brightness(level, display=display_index, method='vcp')
                            return {"success": True, "result": None, "message": f"Яскравість монітора {monitor_id} встановлено на {level} відсотків"}
                        except Exception as fallback_error:
                            print(f"[MONITOR API] VCP метод не спрацював, пробую WMI: {fallback_error}")
                            sbc.set_brightness(level, display=display_index)
                            return {"success": True, "result": None, "message": f"Яскравість монітора {monitor_id} встановлено (резервний метод)."}

            # ==========================================
            # КОМАНДА: ВИМКНЕННЯ МОНІТОРА
            # ==========================================
            elif command_name == "turn_off_monitor":
                monitor_id = str(command_value)
                try:
                    subprocess.run(["MultiMonitorTool.exe", "/disable", monitor_id], check=True)
                    return {"success": True, "result": None, "message": f"Монітор {monitor_id} вимкнено"}
                except FileNotFoundError:
                    return {"success": False, "result": None, "message": "Не знайдено файл MultiMonitorTool.exe для керування живленням."}
                except subprocess.CalledProcessError as e:
                    return {"success": False, "result": None, "message": f"Не вдалося вимкнути монітор: {e}"}

            # ==========================================
            # КОМАНДА: УВІМКНЕННЯ МОНІТОРА
            # ==========================================
            elif command_name == "turn_on_monitor":
                monitor_id = str(command_value)
                try:
                    subprocess.run(["MultiMonitorTool.exe", "/enable", monitor_id], check=True)
                    return {"success": True, "result": None, "message": f"Монітор {monitor_id} увімкнено"}
                except FileNotFoundError:
                    return {"success": False, "result": None, "message": "Не знайдено файл MultiMonitorTool.exe."}
                except subprocess.CalledProcessError as e:
                    return {"success": False, "result": None, "message": f"Не вдалося увімкнути монітор: {e}"}

            return {"success": False, "result": None, "message": f"Невідома команда плагіна: {command_name}"}

        except Exception as e:
            self.log_error(f"Monitor Control Error: {e}")
            return {"success": False, "result": None, "message": f"Внутрішня помилка керування дисплеєм: {str(e)}"}