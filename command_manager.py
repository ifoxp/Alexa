# command_manager.py
import json
import os
import webbrowser
import subprocess
from thefuzz import fuzz, process as fuzzy_process
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

class ActionExecutor:
    # ... (всі методи open_website, run_application і т.д. без змін) ...
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
    # ... і так далі для інших методів

class CommandManager:
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
                        if not command_data.get("name") or not command_data.get("phrases"):
                             print(f"  ⚠️ Пропущено неповний файл: {filename}")
                             continue
                        self.commands.append(command_data)
                        for phrase in command_data['phrases']:
                            self.phrases_map[phrase.lower()] = command_data
                        print(f"  ✅ Завантажено: {command_data['name']}")
                except Exception as e:
                    print(f"  ❌ Помилка завантаження файлу {filename}: {e}")
        print("--- Завантаження команд завершено ---")

    def find_command(self, text):
        text_lower = text.lower()
        commands_with_args = {p: c for p, c in self.phrases_map.items() if c.get("requires_argument")}
        if commands_with_args:
            for phrase, command in commands_with_args.items():
                PARTIAL_THRESHOLD = 90
                # Порівнюємо початок тексту з фразою
                if text_lower.startswith(phrase): # Пробуємо точний збіг спочатку
                    argument = text_lower.replace(phrase, "", 1).strip()
                    if argument:
                        print(f"[DEBUG] Знайдено команду з аргументом (точний збіг): '{command['name']}'")
                        return command, argument
                else: # Якщо точного немає, пробуємо нечіткий
                    text_prefix = text_lower[:len(phrase)]
                    score = fuzz.ratio(text_prefix, phrase)
                    if score >= PARTIAL_THRESHOLD:
                        argument = text_lower[len(phrase):].strip()
                        if argument:
                            print(f"[DEBUG] Знайдено команду з аргументом (нечіткий збіг): '{command['name']}' (Оцінка префіксу: {score}%)")
                            return command, argument

        simple_commands = {p: c for p, c in self.phrases_map.items() if not c.get("requires_argument")}
        if simple_commands:
            result = fuzzy_process.extractOne(text_lower, simple_commands.keys())
            if result:
                best_match_phrase, score = result
                SIMPLE_COMMAND_THRESHOLD = 85
                if score >= SIMPLE_COMMAND_THRESHOLD:
                    command = simple_commands[best_match_phrase]
                    print(f"[DEBUG] Знайдено просту команду: '{command['name']}' (Оцінка: {score}%)")
                    return command, None
        
        print(f"[DEBUG] Команду не знайдено для '{text_lower}'")
        return None, None

    def execute_command(self, command, argument=None):
        actions = command.get("actions")
        if not actions:
            actions = [{"type": command.get("type"), "target": command.get("target")}]

        print(f"--- Виконання команди '{command['name']}' ({len(actions)} дій) ---")
        for action_data in actions:
            command_type = action_data.get("type")
            target = action_data.get("target")
            action_map = {
                "website": lambda: self.action_executor.open_website(target, argument),
                "application": lambda: self.action_executor.run_application(target),
                "script": lambda: self.action_executor.run_script(target),
                "system_volume": lambda: self.action_executor.set_system_volume(argument)
            }
            action_func = action_map.get(command_type)
            if action_func:
                try:
                    action_func()
                except Exception as e:
                    print(f"❌ Помилка під час виконання дії '{command_type}': {e}")
            else:
                print(f"❌ Невідомий тип дії: '{command_type}'")