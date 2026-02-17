import json
import os
import subprocess
import webbrowser
import win32gui
import win32process
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL, cast, POINTER
from thefuzz import process as fuzzy_process
from plugin_system import PluginManager
from logger_config import get_logger
import smart_ai

logger = get_logger('command_manager')

class ActionExecutor:
    """Виконує конкретні дії, визначені командою."""

    def open_website(self, url, argument=None):
        if argument:
            query = "+".join(argument.split())
            webbrowser.open(f"{url}{query}")
            print(f"Відкриваю сайт і шукаю: {argument}")
        else:
            webbrowser.open(url)
            print(f"Відкриваю сайт: {url}")

    def run_application(self, path):
        try:
            # Розширюємо змінні середовища
            expanded_path = os.path.expandvars(path)

            # Якщо це URL - відкриваємо в браузері
            if expanded_path.startswith(('http://', 'https://')):
                webbrowser.open(expanded_path)
                print(f"Відкриваю сайт: {expanded_path}")
                return

            # Спробуємо запустити через Windows Start Menu API (найнадійніший спосіб)
            if self._try_start_app_via_powershell(path):
                print(f"Запустив програму через Start Menu: {path}")
                return

            # Якщо це команда з параметрами
            if ' --' in expanded_path:
                parts = expanded_path.split(' ', 1)
                exe_path = parts[0]
                args = parts[1]
                if os.path.exists(exe_path) or exe_path in ['calc.exe', 'notepad.exe', 'mspaint.exe', 'explorer.exe']:
                    subprocess.Popen(f'"{exe_path}" {args}', shell=True)
                    print(f"Запускаю додаток з параметрами: {exe_path}")
                else:
                    print(f"Помилка: Файл не знайдено за шляхом: {exe_path}")
                return

            # Звичайні exe файли та системні команди
            if os.path.exists(expanded_path) or expanded_path in ['calc.exe', 'notepad.exe', 'mspaint.exe', 'explorer.exe']:
                subprocess.Popen([expanded_path])
                print(f"Запускаю додаток: {expanded_path}")
            else:
                print(f"Помилка: Файл не знайдено за шляхом: {expanded_path}")
        except Exception as e:
            print(f"Помилка при запуску додатку {path}: {e}")

    def _try_start_app_via_powershell(self, app_name):
        """Намагається запустити програму через Windows start команду"""
        try:
            # Якщо це вже повний шлях до exe - не використовуємо start
            if app_name.endswith('.exe') and ('\\' in app_name or '/' in app_name):
                return False

            # Спробуємо декілька варіантів запуску
            methods = [
                # 1. Windows start команда
                ["cmd", "/c", f"start", app_name],
                # 2. Безпосередньо через shell
                ["cmd", "/c", app_name],
                # 3. PowerShell Start-Process
                ["powershell", "-Command", f"Start-Process '{app_name}' -ErrorAction SilentlyContinue"]
            ]

            for method in methods:
                try:
                    result = subprocess.run(
                        method,
                        capture_output=True,
                        text=True,
                        timeout=3,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )

                    if result.returncode == 0:
                        return True

                except Exception:
                    continue

            return False

        except Exception:
            return False

    def run_smart_application(self, command_data, argument):
        """Розумне відкриття програм за назвою."""
        app_mappings = command_data.get("app_mappings", {})
        argument_lower = argument.lower().strip()

        # Шукаємо точний збіг
        if argument_lower in app_mappings:
            target = app_mappings[argument_lower]
            self.run_application(target)
            return

        # Шукаємо часткові збіги
        for app_name, app_path in app_mappings.items():
            if argument_lower in app_name or app_name in argument_lower:
                target = app_mappings[app_name]
                self.run_application(target)
                return

        # Якщо не знайшли - повідомляємо
        available_apps = ", ".join(app_mappings.keys())
        print(f"Програму '{argument}' не знайдено. Доступні програми: {available_apps}")


    def run_script(self, path):
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            subprocess.Popen(['bash', path], creationflags=creationflags)
            print(f"Запускаю скрипт: {path}")
        except Exception as e:
            print(f"Помилка при запуску скрипта {path}: {e}")

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
            print(f"Встановлено загальну гучність на {level}%")
        except Exception as e:
            print(f"Помилка при зміні загальної гучності: {e}")
            
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
                print(f"Встановлено гучність для '{target_session.Process.name()}' на {level}%")
            else:
                print("Не знайдено аудіо-сесію для активного вікна.")
        except Exception as e:
            print(f"Помилка при зміні гучності додатку: {e}")


class CommandManager:
    """Керує завантаженням, пошуком та виконанням команд через plugin систему."""

    def __init__(self, plugins_dir="plugins"):
        # Стара система для зворотної сумісності (минимум)
        self.commands = []
        self.phrases_map = {}
        self.action_executor = ActionExecutor()

        # Нова plugin система (тільки legacy для fallback)
        self.plugin_manager = PluginManager(plugins_dir)
        self.plugin_manager.load_plugins()

        logger.info("Command manager initialized", extra={
            'legacy_plugins': len(self.plugin_manager.get_all_plugins())
        })


    async def find_command(self, text):
        """Шукає команду: спочатку ШІ, потім plugin систему, потім legacy систему."""

        # 1. Спочатку пробуємо ШІ асистента
        if smart_ai.smart_assistant:
            ai_result = await smart_ai.process_smart_command(text)
            if ai_result.get("success"):
                logger.info("Smart plugin command processed", extra={
                    'action_type': ai_result.get('action', {}).get('type'),
                    'successful_count': ai_result.get('action', {}).get('successful_count', 0),
                    'total_count': ai_result.get('action', {}).get('total_count', 0)
                })
                return {'smart_ai': ai_result, 'type': 'smart_ai', 'original_text': text}, None

        # 2. Fallback до plugin системи
        plugin = self.plugin_manager.find_handler(text)
        if plugin:
            logger.debug("Plugin command found", extra={'plugin': plugin.name, 'text': text})
            return {'plugin': plugin, 'type': 'plugin', 'original_text': text}, None

        # 3. Fallback до старої системи
        text_lower = text.lower()

        # Спочатку шукаємо прості команди (без аргументів)
        simple_commands = {p: c for p, c in self.phrases_map.items() if not c.get("requires_argument")}
        if simple_commands:
            # Пошук точних збігів простих команд
            for phrase, command in simple_commands.items():
                if phrase in text_lower:
                    logger.debug("Simple command exact match found", extra={
                        'command': command['name'],
                        'phrase': phrase
                    })
                    return command, None

            # Якщо точний збіг не знайдено, використовуємо нечіткий пошук
            result = fuzzy_process.extractOne(text_lower, simple_commands.keys())
            if result:
                best_match_phrase, score = result
                if score >= 85:
                    command = simple_commands[best_match_phrase]
                    logger.debug("Simple command fuzzy match found", extra={
                        'command': command['name'],
                        'score': score
                    })
                    return command, None

        # Потім шукаємо команди з аргументами
        commands_with_args = {p: c for p, c in self.phrases_map.items() if c.get("requires_argument")}
        if commands_with_args:
            best_command = None
            best_argument = None
            best_phrase_len = 0

            for phrase, command in commands_with_args.items():
                if phrase in text_lower:
                    # Знаходимо позицію фрази
                    phrase_start = text_lower.find(phrase)

                    # Витягуємо аргумент тільки ПІСЛЯ фрази
                    argument = text_lower[phrase_start + len(phrase):].strip()

                    # Вибираємо найдовшу фразу команди (найточніший збіг)
                    if argument and len(phrase) > best_phrase_len:
                        best_command = command
                        best_argument = argument
                        best_phrase_len = len(phrase)

            if best_command:
                logger.debug("Command with argument found", extra={
                    'command': best_command['name'],
                    'argument': best_argument
                })
                return best_command, best_argument

        logger.debug("No command found", extra={'text': text_lower})
        return None, None

    async def execute_command(self, command, argument=None):
        """Виконує команду через нову Smart AI систему або legacy системи."""

        # Перевіряємо чи це Smart AI команда (нова система)
        if isinstance(command, dict) and command.get('type') == 'smart_ai':
            ai_result = command.get('smart_ai', {})

            if ai_result.get('success'):
                return {
                    'success': True,
                    'response_text': ai_result.get('message', 'Smart AI команду виконано')
                }
            else:
                return {
                    'success': False,
                    'response_text': ai_result.get('message', 'Smart AI команда не вдалася')
                }

        # Перевіряємо чи це legacy plugin команда
        if isinstance(command, dict) and command.get('type') == 'legacy_plugin':
            plugin = command['plugin']
            context = {'argument': argument} if argument else {}

            try:
                result = plugin.execute(command.get('original_text', ''), context)

                if result.get('success', False):
                    logger.info("Plugin command executed successfully", extra={
                        'plugin': plugin.name,
                        'message': result.get('message', '')
                    })
                    print(result.get('message', 'Команду виконано'))
                else:
                    logger.warning("Plugin command failed", extra={
                        'plugin': plugin.name,
                        'message': result.get('message', '')
                    })
                    print(result.get('message', 'Помилка виконання команди'))

                return result

            except Exception as e:
                error_msg = f"Помилка виконання plugin команди: {str(e)}"
                logger.error("Plugin execution error", extra={
                    'plugin': plugin.name,
                    'error': str(e)
                })
                print(error_msg)
                return {'success': False, 'message': error_msg}

        # Legacy система
        actions = command.get("actions", [{"type": command.get("type"), "target": command.get("target")}])

        logger.info("Executing legacy command", extra={
            'command': command['name'],
            'actions_count': len(actions)
        })

        for action_data in actions:
            command_type = action_data.get("type")
            target = action_data.get("target")

            action_map = {
                "website": lambda: self.action_executor.open_website(target, argument),
                "application": lambda: self.action_executor.run_application(target),
                "smart_application": lambda: self.action_executor.run_smart_application(command, argument),
                "script": lambda: self.action_executor.run_script(target),
                "system_volume": lambda: self.action_executor.set_system_volume(argument),
                "app_volume": lambda: self.action_executor.set_app_volume(argument)
            }

            action_func = action_map.get(command_type)
            if action_func:
                try:
                    action_func()
                except Exception as e:
                    logger.error("Legacy action execution error", extra={
                        'action_type': command_type,
                        'error': str(e)
                    })
                    print(f"Помилка виконання дії {command_type}: {str(e)}")
            else:
                logger.warning("Unknown action type", extra={'type': command_type})
                print(f"Невідомий тип дії: '{command_type}'")