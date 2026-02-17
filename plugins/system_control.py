# system_control.py
import os
import subprocess
from typing import Dict, Any
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import win32gui
import win32process
from .base_plugin import SmartPlugin


class SystemControlPlugin(SmartPlugin):
    """Плагін для управління системою Windows (звук, файли, процеси)."""

    @property
    def name(self) -> str:
        return "system_control"

    @property
    def description(self) -> str:
        return "Управління системою Windows: звук, файли, процеси. Змінює гучність, відкриває файли, управляє системними функціями."

    @property
    def commands(self) -> Dict[str, str]:
        return {
            "set_volume": "встановити системну гучність (0-100)",
            "volume_up": "збільшити гучність (на скільки)",
            "volume_down": "зменшити гучність (на скільки)",
            "mute_toggle": "увімкнути/вимкнути звук (True/False)",
            "open_file": "відкрити файл чи папку",
            "run_script": "запустити скрипт",
            "get_system_info": "отримати інформацію про систему"
        }

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        """Виконує команду плагіна."""
        try:
            if command_name == "set_volume":
                # Отримуємо значення з різних можливих ключів
                value = kwargs.get("value") or kwargs.get("level", 50)
                if isinstance(value, str) and value.isdigit():
                    value = int(value)
                return await self._set_volume(value)

            elif command_name == "volume_up":
                # Отримуємо значення з різних можливих ключів
                value = kwargs.get("value") or kwargs.get("step", 10)
                if isinstance(value, str) and value.isdigit():
                    value = int(value)
                return await self._volume_up(value)

            elif command_name == "volume_down":
                # Отримуємо значення з різних можливих ключів
                value = kwargs.get("value") or kwargs.get("step", 10)
                if isinstance(value, str) and value.isdigit():
                    value = int(value)
                return await self._volume_down(value)

            elif command_name == "mute_toggle":
                return await self._mute_toggle()

            elif command_name == "open_file":
                return await self._open_file(kwargs.get("path", ""))

            elif command_name == "run_script":
                return await self._run_script(kwargs.get("script_path", ""))

            elif command_name == "get_system_info":
                return await self._get_system_info()

            else:
                return {
                    "success": False,
                    "result": None,
                    "message": f"Невідома команда: {command_name}"
                }

        except Exception as e:
            self.log_error(f"Error executing {command_name}", error=str(e))
            return {
                "success": False,
                "result": None,
                "message": f"Помилка виконання команди: {str(e)}"
            }

    async def _set_volume(self, level: int) -> Dict[str, Any]:
        """Встановлює системну гучність."""
        try:
            if not isinstance(level, int) or not 0 <= level <= 100:
                return {
                    "success": False,
                    "result": None,
                    "message": "Рівень гучності має бути від 0 до 100"
                }

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)

            self.log_info(f"Set system volume to {level}%")

            return {
                "success": True,
                "result": {"volume_level": level},
                "message": f"Встановлено гучність на {level}%"
            }

        except Exception as e:
            self.log_error(f"Failed to set volume to {level}", error=str(e))
            return {
                "success": False,
                "result": None,
                "message": f"Помилка зміни гучності: {str(e)}"
            }

    async def _volume_up(self, step: int) -> Dict[str, Any]:
        """Збільшує гучність."""
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))

            current_level = volume.GetMasterVolumeLevelScalar() * 100
            new_level = min(100, current_level + step)

            volume.SetMasterVolumeLevelScalar(new_level / 100.0, None)

            self.log_info(f"Increased volume by {step}% to {new_level}%")

            return {
                "success": True,
                "result": {"old_level": current_level, "new_level": new_level},
                "message": f"Збільшено гучність на {step}% до {new_level:.0f}%"
            }

        except Exception as e:
            self.log_error(f"Failed to increase volume by {step}", error=str(e))
            return {
                "success": False,
                "result": None,
                "message": f"Помилка збільшення гучності: {str(e)}"
            }

    async def _volume_down(self, step: int) -> Dict[str, Any]:
        """Зменшує гучність."""
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))

            current_level = volume.GetMasterVolumeLevelScalar() * 100
            new_level = max(0, current_level - step)

            volume.SetMasterVolumeLevelScalar(new_level / 100.0, None)

            self.log_info(f"Decreased volume by {step}% to {new_level}%")

            return {
                "success": True,
                "result": {"old_level": current_level, "new_level": new_level},
                "message": f"Зменшено гучність на {step}% до {new_level:.0f}%"
            }

        except Exception as e:
            self.log_error(f"Failed to decrease volume by {step}", error=str(e))
            return {
                "success": False,
                "result": None,
                "message": f"Помилка зменшення гучності: {str(e)}"
            }

    async def _mute_toggle(self) -> Dict[str, Any]:
        """Перемикає звук (mute/unmute)."""
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))

            is_muted = volume.GetMute()
            volume.SetMute(not is_muted, None)

            action = "увімкнено" if is_muted else "вимкнено"
            self.log_info(f"Toggled mute: {action}")

            return {
                "success": True,
                "result": {"was_muted": is_muted, "now_muted": not is_muted},
                "message": f"Звук {action}"
            }

        except Exception as e:
            self.log_error("Failed to toggle mute", error=str(e))
            return {
                "success": False,
                "result": None,
                "message": f"Помилка перемикання звуку: {str(e)}"
            }

    async def _open_file(self, path: str) -> Dict[str, Any]:
        """Відкриває файл або папку."""
        if not path:
            return {
                "success": False,
                "result": None,
                "message": "Шлях до файлу не може бути пустим"
            }

        try:
            expanded_path = os.path.expandvars(path)

            if os.path.exists(expanded_path):
                os.startfile(expanded_path)
                self.log_info(f"Opened file: {expanded_path}")

                return {
                    "success": True,
                    "result": {"path": expanded_path},
                    "message": f"Відкрито файл: {expanded_path}"
                }
            else:
                return {
                    "success": False,
                    "result": None,
                    "message": f"Файл не знайдено: {expanded_path}"
                }

        except Exception as e:
            self.log_error(f"Failed to open file: {path}", error=str(e))
            return {
                "success": False,
                "result": None,
                "message": f"Помилка відкриття файлу: {str(e)}"
            }

    async def _run_script(self, script_path: str) -> Dict[str, Any]:
        """Запускає скрипт."""
        if not script_path:
            return {
                "success": False,
                "result": None,
                "message": "Шлях до скрипту не може бути пустим"
            }

        try:
            expanded_path = os.path.expandvars(script_path)

            if not os.path.exists(expanded_path):
                return {
                    "success": False,
                    "result": None,
                    "message": f"Скрипт не знайдено: {expanded_path}"
                }

            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

            if expanded_path.endswith('.py'):
                subprocess.Popen(['python', expanded_path], creationflags=creationflags)
            elif expanded_path.endswith('.bat') or expanded_path.endswith('.cmd'):
                subprocess.Popen([expanded_path], shell=True, creationflags=creationflags)
            elif expanded_path.endswith('.sh'):
                subprocess.Popen(['bash', expanded_path], creationflags=creationflags)
            else:
                subprocess.Popen([expanded_path], creationflags=creationflags)

            self.log_info(f"Executed script: {expanded_path}")

            return {
                "success": True,
                "result": {"script_path": expanded_path},
                "message": f"Запущено скрипт: {expanded_path}"
            }

        except Exception as e:
            self.log_error(f"Failed to run script: {script_path}", error=str(e))
            return {
                "success": False,
                "result": None,
                "message": f"Помилка запуску скрипту: {str(e)}"
            }

    async def _get_system_info(self) -> Dict[str, Any]:
        """Отримує базову інформацію про систему."""
        try:
            import platform
            import psutil

            info = {
                "system": platform.system(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "memory_total": psutil.virtual_memory().total // (1024**3),  # GB
                "memory_available": psutil.virtual_memory().available // (1024**3),  # GB
                "disk_usage": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
            }

            return {
                "success": True,
                "result": info,
                "message": f"Система: {info['system']} {info['version']}, ОЗП: {info['memory_available']}/{info['memory_total']} GB"
            }

        except Exception as e:
            self.log_error("Failed to get system info", error=str(e))
            return {
                "success": False,
                "result": None,
                "message": f"Помилка отримання інформації про систему: {str(e)}"
            }