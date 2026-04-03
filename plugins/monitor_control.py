import os
import json
import subprocess
import screen_brightness_control as sbc
from typing import Dict, Any
from .base_plugin import SmartPlugin

class MonitorControlPlugin(SmartPlugin):
    """Плагін для керування моніторами: яскравість та живлення через DDC/CI та MultiMonitorTool."""

    def __init__(self):
        super().__init__()
        # Перевіряємо монітори при старті ядра
        try:
            self.monitors = sbc.list_monitors()
            print(f"[MONITOR PLUGIN] Ініціалізація. Знайдено моніторів: {len(self.monitors)}")
            for i, name in enumerate(self.monitors):
                print(f"  -> Індекс [{i}]: {name}")
        except Exception as e:
            print(f"[ERROR] Failed to list monitors on init: {e}")
            self.monitors = []

    @property
    def name(self) -> str:
        return "monitor_control"

    @property
    def description(self) -> str:
        return "Керування моніторами: зміна яскравості конкретного монітора, вимкнення або увімкнення екранів."
    
    @property
    def commands(self) -> Dict[str, str]:
        return {
            "set_brightness": "встановити яскравість. Значення — масив [номер, відсоток]. Якщо моніторів КІЛЬКА з РІЗНОЮ яскравістю, передавай масив масивів. Приклади: {'set_brightness': [2, 30]} (один), {'set_brightness': [[1, 55], [2, 30]]} (кілька), або {'set_brightness': ['all', 50]} (всі).",
            "turn_off_monitor": "вимкнути монітор. Значення — номер монітора. Приклад: {'turn_off_monitor': 2}",
            "turn_on_monitor": "увімкнути монітор. Значення — номер монітора. Приклад: {'turn_on_monitor': 1}"
        }

    def _get_tool_path(self) -> str:
        """Повертає абсолютний шлях до MultiMonitorTool.exe, який лежить у цій же папці."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "MultiMonitorTool.exe")

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        try:
            value_field = kwargs.get("value")
            level_field = kwargs.get("level")
            print(f"[MONITOR] execute: command={command_name}, value='{value_field}', level='{level_field}'")

            available_monitors = sbc.list_monitors()
            print(f"[MONITOR] monitors found: {len(available_monitors)} {available_monitors}")

            # ==========================================
            # КОМАНДИ: ЖИВЛЕННЯ (УВІМКНЕННЯ / ВИМКНЕННЯ)
            # ==========================================
            if command_name in ["turn_off_monitor", "turn_on_monitor"]:
                # Беремо номер монітора з value, а якщо там пусто — беремо з level
                raw_monitor_id = value_field if value_field else level_field
                monitor_id = str(raw_monitor_id).strip()
                print(f"[MONITOR] power command: monitor_id='{monitor_id}', action={command_name}")

                tool_path = self._get_tool_path()
                print(f"[MONITOR] tool path: '{tool_path}'")
                
                if not os.path.exists(tool_path):
                    print(f"[ERROR] Файл не знайдено за шляхом: {tool_path}")
                    return {"success": False, "result": None, "message": "Файл MultiMonitorTool.exe не знайдено у папці з плагіном."}
                
                # Змінили /disable на /TurnOff, а /enable на /TurnOn
                # Тепер монітор просто "засинає", зберігаючи свою вертикальну орієнтацію!
                action = "/TurnOff" if command_name == "turn_off_monitor" else "/TurnOn"
                cmd_list = [tool_path, action, monitor_id]
                print(f"[MONITOR] running: {cmd_list}")

                try:
                    subprocess.run(cmd_list, check=True, capture_output=True, text=True)
                    status_msg = "вимкнено" if command_name == "turn_off_monitor" else "увімкнено"
                    print(f"[MONITOR] monitor {monitor_id} {status_msg}")
                    return {"success": True, "result": None, "message": f"Монітор {monitor_id} {status_msg}"}
                except subprocess.CalledProcessError as e:
                    print(f"[MONITOR] command failed (rc={e.returncode}): {e.stderr}")
                    return {"success": False, "result": None, "message": f"Не вдалося змінити стан монітора: {e}"}

            # ==========================================
            # КОМАНДА: ЗМІНА ЯСКРАВОСТІ
            # ==========================================
            elif command_name == "set_brightness":
                if not available_monitors:
                    return {"success": False, "result": None, "message": "Система не бачить дисплеїв для зміни яскравості."}

                command_value = None
                # Формуємо правильний масив для яскравості
                if level_field and "," in str(level_field):
                    parts = str(level_field).split(",")
                    command_value = [parts[0].strip(), parts[1].strip()]
                elif value_field:
                    command_value = value_field
                elif level_field:
                    command_value = level_field

                print(f"[MONITOR] set_brightness raw value: {command_value}")

                if isinstance(command_value, str):
                    try:
                        command_value = json.loads(command_value.replace("'", '"'))
                    except (json.JSONDecodeError, ValueError):
                        pass

                print(f"[MONITOR] set_brightness parsed: {command_value} (type={type(command_value).__name__})")

                if not isinstance(command_value, list):
                    print(f"[MONITOR] expected list, got {type(command_value).__name__}")
                    return {"success": False, "result": None, "message": "Неправильний формат параметрів. Очікувався масив."}

                # СЦЕНАРІЙ 1: Масив масивів (кілька моніторів з різною яскравістю)
                if len(command_value) > 0 and isinstance(command_value[0], list):
                    success_msgs = []
                    for item in command_value:
                        if len(item) >= 2:
                            mon_id = item[0]
                            lvl = int(item[1])
                            disp_idx = int(mon_id) - 1
                            if disp_idx < 0 or disp_idx >= len(available_monitors):
                                continue
                            try:
                                print(f"[MONITOR] set brightness monitor {mon_id} (idx={disp_idx}) -> {lvl}%")
                                sbc.set_brightness(lvl, display=disp_idx, method='vcp')
                                success_msgs.append(f"М{mon_id}: {lvl}%")
                            except Exception as e:
                                print(f"[MONITOR] VCP failed for monitor {mon_id}: {e}, trying fallback")
                                try:
                                    sbc.set_brightness(lvl, display=disp_idx)
                                    success_msgs.append(f"М{mon_id}: {lvl}% (резерв)")
                                except Exception:
                                    pass
                    print(f"[MONITOR] multi-monitor brightness done: {success_msgs}")
                    return {"success": True, "result": None, "message": f"Оновлено яскравість: {', '.join(success_msgs)}"}

                # СЦЕНАРІЙ 2: Одинарний масив (один монітор або всі)
                elif len(command_value) >= 2:
                    monitor_id = command_value[0]
                    level = int(command_value[1])

                    if str(monitor_id).lower() == "all":
                        print(f"[MONITOR] set brightness ALL monitors -> {level}%")
                        for i in range(len(available_monitors)):
                            try:
                                sbc.set_brightness(level, display=i, method='vcp')
                            except Exception:
                                sbc.set_brightness(level, display=i)
                        return {"success": True, "result": None, "message": f"Яскравість всіх дисплеїв встановлено на {level}%"}

                    else:
                        display_index = int(monitor_id) - 1
                        if display_index < 0 or display_index >= len(available_monitors):
                            print(f"[MONITOR] monitor {monitor_id} not found (total={len(available_monitors)})")
                            return {"success": False, "result": None, "message": f"Монітор з номером {monitor_id} не знайдено."}

                        try:
                            print(f"[MONITOR] set brightness monitor {monitor_id} (idx={display_index}) -> {level}%")
                            sbc.set_brightness(level, display=display_index, method='vcp')
                            return {"success": True, "result": None, "message": f"Яскравість монітора {monitor_id} встановлено на {level}%"}
                        except Exception as fallback_error:
                            print(f"[MONITOR] VCP failed: {fallback_error}, trying fallback")
                            sbc.set_brightness(level, display=display_index)
                            return {"success": True, "result": None, "message": f"Яскравість монітора {monitor_id} встановлено (резерв)."}

            print(f"[MONITOR] unknown command: {command_name}")
            return {"success": False, "result": None, "message": f"Невідома команда: {command_name}"}

        except Exception as e:
            print(f"[MONITOR] critical error: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "result": None, "message": f"Внутрішня помилка: {str(e)}"}

      