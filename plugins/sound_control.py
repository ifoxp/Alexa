# sound_control.py
import os
import traceback
import psutil
import difflib  # Для пошуку схожих назв
from typing import Dict, Any, List, Tuple
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume, ISimpleAudioVolume
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
import win32gui
import win32process
from .base_plugin import SmartPlugin

class SystemControlPlugin(SmartPlugin):
    """Плагін для управління гучністю системи та конкретних програм."""

    @property
    def name(self) -> str:
        return "sound_control"

    @property
    def description(self) -> str:
        return "Управління гучністю: системи, активного вікна або конкретної програми за назвою."

    @property
    def commands(self) -> Dict[str, str]:
        return {
            "set_volume": "встановити загальну гучність (0-100)",
            "volume_up": "збільшити загальну гучність (на скільки)",
            "volume_down": "зменшити загальну гучність (на скільки)",
            "mute_toggle": "увімкнути/вимкнути звук",
            "set_active_app_volume": "встановити гучність активного вікна (0-100)",
            "set_specific_app_volume": "встановити гучність програми (назва програми і рівень, наприклад 'Spotify 50')"
        }

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        try:
            # Отримання значення (універсальне)
            raw_value = kwargs.get("value") or kwargs.get("level") or kwargs.get("step")
            
            # Базовий парсинг числа (якщо прийшло просто число)
            value_int = 0
            if raw_value:
                if isinstance(raw_value, (int, float)):
                    value_int = int(raw_value)
                elif isinstance(raw_value, str) and raw_value.isdigit():
                    value_int = int(raw_value)

            if command_name == "set_volume":
                return await self._set_volume(value_int if value_int else 50)
            
            elif command_name == "volume_up":
                return await self._volume_up(value_int if value_int else 10)
            
            elif command_name == "volume_down":
                return await self._volume_down(value_int if value_int else 10)
            
            elif command_name == "mute_toggle":
                return await self._mute_toggle()
            
            elif command_name == "set_active_app_volume":
                return await self._set_active_app_volume(value_int)

            elif command_name == "set_specific_app_volume":
                # Тут raw_value може бути "Steam 24" або "Spotify 100"
                # Нам треба розпарсити це
                if isinstance(raw_value, str):
                    return await self._set_specific_app_volume_by_text(raw_value)
                else:
                     return {"success": False, "message": "Для цієї команди потрібна назва програми"}

            else:
                return {"success": False, "result": None, "message": f"Невідома команда: {command_name}"}

        except Exception as e:
            traceback.print_exc()
            return {"success": False, "result": None, "message": f"Помилка: {str(e)}"}

    # --- Standard System Volume Methods ---
    async def _set_volume(self, level: int) -> Dict[str, Any]:
        try:
            level = max(0, min(100, level))
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            return {"success": True, "result": {"volume_level": level}, "message": f"Встановлено загальну гучність на {level}%"}
        except Exception as e:
            return {"success": False, "result": None, "message": f"Помилка: {str(e)}"}

    async def _volume_up(self, step: int) -> Dict[str, Any]:
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            current_level = volume.GetMasterVolumeLevelScalar() * 100
            new_level = min(100, current_level + step)
            volume.SetMasterVolumeLevelScalar(new_level / 100.0, None)
            return {"success": True, "result": {"level": new_level}, "message": f"Гучність збільшено до {new_level:.0f}%"}
        except Exception:
            return {"success": False, "message": "Помилка зміни гучності"}

    async def _volume_down(self, step: int) -> Dict[str, Any]:
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            current_level = volume.GetMasterVolumeLevelScalar() * 100
            new_level = max(0, current_level - step)
            volume.SetMasterVolumeLevelScalar(new_level / 100.0, None)
            return {"success": True, "result": {"level": new_level}, "message": f"Гучність зменшено до {new_level:.0f}%"}
        except Exception:
            return {"success": False, "message": "Помилка зміни гучності"}

    async def _mute_toggle(self) -> Dict[str, Any]:
        try:
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            is_muted = volume.GetMute()
            volume.SetMute(not is_muted, None)
            state = "увімкнено" if is_muted else "вимкнено"
            return {"success": True, "result": {"muted": not is_muted}, "message": f"Звук {state}"}
        except Exception as e:
            return {"success": False, "message": f"Помилка: {e}"}

    # --- Advanced App Control Methods ---

    async def _set_active_app_volume(self, level: int) -> Dict[str, Any]:
        """Встановлює гучність для активного вікна."""
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, active_pid = win32process.GetWindowThreadProcessId(hwnd)
            window_title = win32gui.GetWindowText(hwnd) or "Unknown Window"
            
            # Отримуємо ім'я процесу активного вікна
            active_exe_name = ""
            try:
                active_exe_name = psutil.Process(active_pid).name().lower()
            except: pass

            level = max(0, min(100, int(level)))
            sessions = AudioUtilities.GetAllSessions()
            app_found = False
            
            for session in sessions:
                if not session or session.ProcessId == 0: continue
                try:
                    session_pid = session.ProcessId
                    session_proc = psutil.Process(session_pid)
                    session_exe_name = session_proc.name().lower()

                    if session_pid == active_pid or (active_exe_name and session_exe_name == active_exe_name):
                        volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                        volume.SetMasterVolume(level / 100.0, None)
                        app_found = True
                except: continue
            
            if app_found:
                return {"success": True, "message": f"Гучність '{window_title}' встановлено на {level}%"}
            else:
                return {"success": False, "message": f"Не знайдено аудіо для '{window_title}'"}

        except Exception as e:
            return {"success": False, "message": f"Помилка: {str(e)}"}

    async def _set_specific_app_volume_by_text(self, text: str) -> Dict[str, Any]:
        """
        Парсить рядок 'Steam 50', знаходить програму і ставить гучність.
        """
        try:
            # 1. Розділяємо назву і число
            # Шукаємо останнє число в рядку
            parts = text.split()
            app_query = ""
            level = 50

            # Якщо останнє слово - це число, беремо його як гучність
            if parts[-1].isdigit():
                level = int(parts[-1])
                app_query = " ".join(parts[:-1]).lower()
            else:
                # Якщо числа немає, беремо весь текст як назву
                app_query = text.lower()
            
            level = max(0, min(100, level))
            
            print(f"[DEBUG] Search Query: '{app_query}', Target Level: {level}")

            # 2. Отримуємо список всіх програм зі звуком
            sessions = AudioUtilities.GetAllSessions()
            audio_apps = {} # map: simple_name -> [session_objects]

            for session in sessions:
                if not session or session.ProcessId == 0: continue
                try:
                    proc = psutil.Process(session.ProcessId)
                    exe_name = proc.name().lower() # spotify.exe
                    simple_name = exe_name.replace(".exe", "") # spotify
                    
                    if simple_name not in audio_apps:
                        audio_apps[simple_name] = []
                    audio_apps[simple_name].append(session)
                except: continue

            available_apps = list(audio_apps.keys())
            print(f"[DEBUG] Available audio apps: {available_apps}")

            # 3. Fuzzy matching (шукаємо найбільш схожу назву)
            # Використовуємо difflib для пошуку (cutoff=0.4 означає 40% схожості мінімум)
            matches = difflib.get_close_matches(app_query, available_apps, n=1, cutoff=0.4)

            target_app_name = None
            
            # Спеціальні перевірки для популярних скорочень
            if not matches:
                if "chrome" in app_query and "chrome" in available_apps: target_app_name = "chrome"
                elif "discord" in app_query and "discord" in available_apps: target_app_name = "discord"
                elif "steam" in app_query:
                    # Steam часто має процеси типу steamwebhelper
                    for app in available_apps:
                        if "steam" in app: 
                            target_app_name = app
                            break
            else:
                target_app_name = matches[0]

            if target_app_name:
                print(f"[DEBUG] Match found: '{app_query}' -> '{target_app_name}'")
                
                # Застосовуємо гучність до всіх сесій цієї програми
                target_sessions = audio_apps[target_app_name]
                for session in target_sessions:
                    volume = session._ctl.QueryInterface(ISimpleAudioVolume)
                    volume.SetMasterVolume(level / 100.0, None)
                
                return {
                    "success": True, 
                    "message": f"Гучність для '{target_app_name}' встановлено на {level}%"
                }
            else:
                return {
                    "success": False, 
                    "message": f"Програму '{app_query}' не знайдено серед активних аудіо джерел. Доступні: {', '.join(available_apps[:5])}..."
                }

        except Exception as e:
            traceback.print_exc()
            return {"success": False, "message": f"Помилка пошуку програми: {e}"}