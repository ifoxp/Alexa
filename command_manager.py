import json
import os
import webbrowser
import subprocess
from thefuzz import fuzz, process as fuzzy_process
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import win32gui
import win32process

class ActionExecutor:
    """Виконує конкретні дії, визначені командою."""

    def open_website(self, url, argument=None):
        if argument:
            query = "+".join(argument.split())
            webbrowser.open(f"{url}{query}")
            print(f"🌐 Відкриваю сайт і шукаю: {argument}")
        else:
            webbrowser.open(url)
            print(f"🌐 Відкриваю сайт: {url}")

    def run_application(self, path):
        try:
            if not os.path.exists(path):
                print(f"❌ Помилка: Файл не знайдено за шляхом: {path}")
                return
            subprocess.Popen([path])
            print(f"🚀 Запускаю додаток: {path}")
        except Exception as e:
            print(f"❌ Помилка при запуску додатку {path}: {e}")

    def run_script(self, path):
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            subprocess.Popen(['bash', path], creationflags=creationflags)
            print(f"📜 Запускаю скрипт: {path}")
        except Exception as e:
            print(f"❌ Помилка при запуску скрипта {path}: {e}")

    def set_system_volume(self, argument):
        try:
            level_str = ''.join(filter(str.isdigit, argument))
            if not level_str: return
            level = int(level_str)
            if not 0 <= level <= 100: return

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            print(f"🔊 Встановлено загальну гучність на {level}%")
        except Exception as e:
            print(f"❌ Помилка при зміні загальної гучності: {e}")
            
    def set_app_volume(self, argument):
        """Встановлює гучність для активного додатку."""
        try:
            level_str = ''.join(filter(str.isdigit, argument))
            if not level_str: return
            level = int(level_str)
            if not 0 <= level <= 100: return

            pid = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())[-1]
            sessions = AudioUtilities.GetAllSessions()
            target_session = None
            for session in sessions:
                if session.Process and session.Process.pid == pid:
                    target_session = session
                    break
            
            if target_session:
                volume = target_session.SimpleAudioVolume
                volume.SetMasterVolume(level / 100.0, None)
                print(f"🔊 Встановлено гучність для '{target_session.Process.name()}' на {level}%")
            else:
                print("❌ Не знайдено аудіо-сесію для активного вікна.")
        except Exception as e:
            print(f"❌ Помилка при зміні гучності додатку: {e}")


class CommandManager:
    """Керує завантаженням, пошуком та виконанням команд."""

    def __init__(self, commands_dir="commands"):
        self.commands = []
        self.phrases_map = {}
        self.action_executor = ActionExecutor()
        self.load_commands(commands_dir)

    def load_commands(self, commands_dir):
        print(f"--- Завантаження команд з '{commands_dir}' ---")
        if not os.path.exists(commands_dir):
            print(f"⚠️ Папка '{commands_dir}' не знайдена. Команди не завантажено.")
            return

        for filename in os.listdir(commands_dir):
            if filename.endswith("_command.json"):
                path = os.path.join(commands_dir, filename)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        command_data = json.load(f)
                        self.commands.append(command_data)
                        for phrase in command_data['phrases']:
                            self.phrases_map[phrase.lower()] = command_data
                        print(f"  ✅ Завантажено: {command_data['name']}")
                except Exception as e:
                    print(f"  ❌ Помилка завантаження файлу {filename}: {e}")
        print("--- Завантаження команд завершено ---")

    def find_command(self, text):
        text_lower = text.lower()
        
        # --- Пріоритет №1: Пошук команд, що вимагають аргумент ---
        commands_with_args = {p: c for p, c in self.phrases_map.items() if c.get("requires_argument")}
        if commands_with_args:
            for phrase, command in commands_with_args.items():
                if text_lower.startswith(phrase):
                    argument = text_lower.replace(phrase, "", 1).strip()
                    if argument:
                        print(f"[DEBUG] Знайдено команду з аргументом: '{command['name']}'")
                        return command, argument

        # --- Пріоритет №2: Нечіткий пошук для простих команд ---
        simple_commands = {p: c for p, c in self.phrases_map.items() if not c.get("requires_argument")}
        if simple_commands:
            result = fuzzy_process.extractOne(text_lower, simple_commands.keys())
            if result:
                best_match_phrase, score = result
                if score >= 85:
                    command = simple_commands[best_match_phrase]
                    print(f"[DEBUG] Знайдено просту команду: '{command['name']}' (Оцінка: {score}%)")
                    return command, None
        
        # !!! ВИПРАВЛЕНО: Гарантуємо, що завжди повертається tuple !!!
        print(f"[DEBUG] Команду не знайдено для '{text_lower}'")
        return None, None

    def execute_command(self, command, argument=None):
        actions = command.get("actions", [{"type": command.get("type"), "target": command.get("target")}])

        print(f"--- Виконання команди '{command['name']}' ({len(actions)} дій) ---")
        for action_data in actions:
            command_type = action_data.get("type")
            target = action_data.get("target")

            action_map = {
                "website": lambda: self.action_executor.open_website(target, argument),
                "application": lambda: self.action_executor.run_application(target),
                "script": lambda: self.action_executor.run_script(target),
                "system_volume": lambda: self.action_executor.set_system_volume(argument),
                "app_volume": lambda: self.action_executor.set_app_volume(argument)
            }

            action_func = action_map.get(command_type)
            if action_func:
                action_func()
            else:
                print(f"❌ Невідомий тип дії: '{command_type}'")