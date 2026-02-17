import json
import asyncio
import os
import winreg
import subprocess
from pathlib import Path
from openai import AsyncOpenAI
from logger_config import get_logger

logger = get_logger('smart_ai')

def scan_installed_programs():
    """Сканує встановлені програми через Windows Search та реєстр"""
    programs = {}

    try:
        # 1. Пошук через Windows Registry (Start Menu programs)
        logger.info("Searching programs via Windows Registry...")
        programs.update(_scan_registry_programs())

        # 2. Пошук через PowerShell Get-StartApps (найнадійніший)
        logger.info("Searching programs via PowerShell Get-StartApps...")
        programs.update(_scan_powershell_programs())

        # 3. Додаткові системні програми
        system_programs = {
            "calculator": "calc.exe",
            "калькулятор": "calc.exe",
            "notepad": "notepad.exe",
            "блокнот": "notepad.exe",
            "paint": "mspaint.exe",
            "explorer": "explorer.exe",
            "провідник": "explorer.exe",
            "файли": "explorer.exe",
            "cmd": "cmd.exe",
            "terminal": "wt.exe",
            "powershell": "powershell.exe"
        }
        programs.update(system_programs)

        logger.info(f"Found {len(programs)} total programs")

    except Exception as e:
        logger.error(f"Error scanning programs: {e}")

    return programs

def _scan_registry_programs():
    """Сканує програми через реєстр Windows"""
    programs = {}

    try:
        # Uninstall registry keys
        registry_paths = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ]

        for reg_path in registry_paths:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        subkey = winreg.OpenKey(key, subkey_name)

                        try:
                            display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                            install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]

                            # Перевіряємо чи є exe файли в директорії
                            if install_location and os.path.exists(install_location):
                                for file in os.listdir(install_location):
                                    if file.lower().endswith('.exe'):
                                        exe_path = os.path.join(install_location, file)
                                        app_key = display_name.lower().replace(' ', '_')
                                        programs[app_key] = exe_path
                                        break
                        except FileNotFoundError:
                            pass
                        except OSError:
                            pass

                        winreg.CloseKey(subkey)
                    except Exception:
                        continue
                winreg.CloseKey(key)
            except Exception:
                continue

    except Exception as e:
        logger.error(f"Registry scan error: {e}")

    return programs

def _scan_powershell_programs():
    """Використовує PowerShell Get-StartApps для пошуку програм"""
    programs = {}

    try:
        # PowerShell команда для отримання всіх Start Menu програм
        ps_command = "Get-StartApps | Where-Object {$_.AppID -like '*.exe*' -or $_.AppID -like '*\\*'} | Select-Object Name, AppID | ConvertTo-Json"

        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0 and result.stdout.strip():
            try:
                apps_data = json.loads(result.stdout)
                if isinstance(apps_data, dict):
                    apps_data = [apps_data]  # Якщо один елемент

                for app in apps_data:
                    name = app.get('Name', '').lower()
                    app_id = app.get('AppID', '')

                    if name and app_id:
                        # Мапінг популярних програм
                        name_mappings = {
                            'telegram': ['telegram'],
                            'chrome': ['chrome', 'google chrome'],
                            'firefox': ['firefox', 'mozilla firefox'],
                            'discord': ['discord'],
                            'steam': ['steam'],
                            'spotify': ['spotify'],
                            'vlc': ['vlc'],
                            'obs': ['obs studio'],
                            'zoom': ['zoom'],
                            'teams': ['microsoft teams'],
                            'vscode': ['visual studio code'],
                            'notepad++': ['notepad++'],
                            'winrar': ['winrar'],
                            '7zip': ['7-zip']
                        }

                        for key, search_terms in name_mappings.items():
                            if any(term in name for term in search_terms):
                                programs[key] = app_id
                                logger.debug(f"Found {key} via PowerShell: {app_id}")
                                break

                        # Також зберігаємо оригінальну назву
                        clean_name = name.replace(' ', '_').replace('-', '_')
                        programs[clean_name] = app_id

            except json.JSONDecodeError as e:
                logger.error(f"PowerShell JSON decode error: {e}")

    except Exception as e:
        logger.error(f"PowerShell scan error: {e}")

    return programs

class SmartAssistant:
    def __init__(self, api_key, model="gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

        # Сканування встановлених програм
        logger.info("Scanning installed programs...")
        self.installed_programs = scan_installed_programs()
        logger.info(f"Found {len(self.installed_programs)} programs", extra={'programs': list(self.installed_programs.keys())})




    async def select_plugins(self, user_text: str):
        """ЕТАП 1: GPT обирає потрібні плагіни для обробки команди."""
        try:
            logger.info("Starting plugin selection", extra={'user_text': user_text})

            plugins_summary = self.plugin_manager.get_plugins_summary()
            logger.info("Got plugins summary", extra={'plugins_count': len(plugins_summary)})

            plugins_list = []
            for i, plugin in enumerate(plugins_summary, 1):
                try:
                    plugin_desc = plugin['description']
                    plugin_line = f"{i}. {plugin_desc}"
                    plugins_list.append(plugin_line)
                except Exception as e:
                    logger.error(f"Error processing plugin: {e}")

            plugins_text = '\n'.join(plugins_list)

            prompt = f"""Ти розумний голосовий асистент. Користувач каже: "{user_text}"

ДОСТУПНІ ПЛАГІНИ:
{plugins_text}

Твоя задача: проаналізувати команду і повернути JSON зі списком потрібних плагінів.

ФОРМАТ ВІДПОВІДІ (тільки JSON):
{{"success": true, "plugins": ["назва_плагіна1", "назва_плагіна2"], "confidence": 0.95}}

ПРИКЛАДИ:
"запусти телеграм" → {{"success": true, "plugins": ["windows_programs"], "confidence": 0.95}}
"знайди котиків на ютубі" → {{"success": true, "plugins": ["browser_search"], "confidence": 0.90}}
"запусти телеграм і знайди музику" → {{"success": true, "plugins": ["windows_programs", "browser_search"], "confidence": 0.85}}
"зроби тихіше" → {{"success": true, "plugins": ["system_control"], "confidence": 0.95}}

confidence: від 0.0 до 1.0"""

            # Простий промпт для вибору плагінів
            simple_prompt = f"""Користувач каже: "{user_text}"

Список плагінів:
{plugins_text}

Дай номери плагінів які підходять під цей запит.
Відповідь у форматі JSON: {{"plugins": [1,2,3]}}

Приклади:
"запусти telegram і зроби звук на 50%" -> {{"plugins": [1,2]}}
"знайди котиків на youtube" -> {{"plugins": [2]}}
"відкрий браузер" -> {{"plugins": [1]}}"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a smart assistant that analyzes user commands and selects appropriate plugins."},
                    {"role": "user", "content": simple_prompt}
                ],
                max_tokens=150
            )

            result_text = response.choices[0].message.content.strip()
            logger.info("GPT plugin selection result", extra={'response': result_text})

            # Перевіряємо чи відповідь не пуста
            if not result_text:
                logger.error("Empty response from GPT-5, falling back to GPT-4o-mini for stage 1")
                # Fallback на GPT-4o-mini
                response = await self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a smart assistant that analyzes user commands and selects appropriate plugins."},
                        {"role": "user", "content": simple_prompt}
                    ],
                    max_tokens=150
                )
                result_text = response.choices[0].message.content.strip()
                logger.info("Fallback GPT-4o-mini plugin selection result", extra={'response': result_text})

            if not result_text:
                return {"success": False, "error": "Empty response from both GPT-5 and GPT-4o-mini"}

            try:
                result = json.loads(result_text)
                plugin_numbers = result.get("plugins", [])

                if plugin_numbers:
                    # Конвертуємо номери в назви плагінів
                    selected_plugin_names = []
                    for num in plugin_numbers:
                        try:
                            plugin_index = num - 1  # Номери починаються з 1
                            if 0 <= plugin_index < len(plugins_summary):
                                plugin_name = plugins_summary[plugin_index]['name']
                                selected_plugin_names.append(plugin_name)
                        except (IndexError, KeyError):
                            continue

                    if selected_plugin_names:
                        return {"success": True, "plugins": selected_plugin_names}

                return {"success": False, "error": "No valid plugins selected"}
            except json.JSONDecodeError as e:
                return {"success": False, "error": "Invalid JSON response"}

        except Exception as e:
            import traceback
            error_type = type(e).__name__
            error_msg = str(e)

            # Специфічні повідомлення для різних типів помилок
            if "401" in error_msg or "Unauthorized" in error_msg:
                user_friendly_msg = "Помилка авторизації OpenAI API. Перевірте API ключ у config.json"
                logger.error("OpenAI API authorization failed", extra={'error': error_msg})
            elif "timeout" in error_msg.lower() or "TimeoutError" in error_type:
                user_friendly_msg = "Таймаут з'єднання з OpenAI API"
                logger.error("OpenAI API timeout", extra={'error': error_msg})
            elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                user_friendly_msg = "Проблеми з підключенням до OpenAI API"
                logger.error("OpenAI API connection error", extra={'error': error_msg})
            elif "Empty response" in error_msg:
                # Спробуємо fallback режим
                manual_result = analyze_command_manually(user_text)
                if manual_result.get("success"):
                    return manual_result
                else:
                    user_friendly_msg = "OpenAI повернув пусту відповідь і команду не вдалося розпізнати автоматично"
            else:
                user_friendly_msg = f"Помилка ШІ асистента: {error_msg}"
                logger.error("Plugin selection failed", extra={'error': error_msg})

            return {"success": False, "error": user_friendly_msg}

    async def execute_plugin_commands(self, user_text: str, selected_plugins: list):
        """ЕТАП 2: Для обраних плагінів визначаємо команди та їх параметри."""
        execution_plan = []

        # Збираємо всі команди від усіх обраних плагінів в один список
        all_commands = []
        plugin_command_map = {}  # Мапа: команда -> плагін

        for plugin_name in selected_plugins:
            plugin_info = self.plugin_manager.get_plugin_commands(plugin_name)
            if not plugin_info:
                continue

            for cmd_name, cmd_desc in plugin_info['commands'].items():
                all_commands.append(f"- {cmd_name}: {cmd_desc} [{plugin_name}]")
                plugin_command_map[cmd_name] = plugin_name

        if not all_commands:
            return []

        commands_text = '\n'.join(all_commands)

        prompt = f"""Користувач каже: "{user_text}"

Доступні команди:
{commands_text}

Твоя задача підібрати команди які підходять під запит і написати їх у форматі JSON.
ВАЖЛИВО: витягуй точні значення параметрів з тексту користувача!

ДЛЯ МНОЖИННИХ ПРОГРАМ використовуй нумеровані ключі:

Приклади:
"запусти Steam і зроби звук на 77%" -> {{"open_program": "Steam", "set_volume": "77"}}
"відкрий Steam Epic Games Spotify і Word" -> {{"open_program1": "Steam", "open_program2": "Epic Games", "open_program3": "Spotify", "open_program4": "Word"}}
"знайди котиків на youtube" -> {{"search_youtube": "котики"}}
"зроби тихіше на 20" -> {{"volume_down": "20"}}

Формат відповіді: {{"команда1": "параметр1", "команда2": "параметр2"}}"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a smart assistant that generates specific plugin commands. Extract exact parameter values from user text."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200
            )

            result_text = response.choices[0].message.content.strip()
            logger.info(f"Stage 2 AI response: '{result_text}'")

            if not result_text:
                logger.error("Empty response from GPT-5, falling back to GPT-4o-mini")
                # Fallback на GPT-4o-mini
                response = await self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a smart assistant that generates specific plugin commands. Extract exact parameter values from user text."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200
                )
                result_text = response.choices[0].message.content.strip()
                logger.info(f"Fallback GPT-4o-mini response: '{result_text}'")

            commands_dict = json.loads(result_text)

            # Групуємо команди за плагінами
            plugin_commands = {}

            for command_name, param_value in commands_dict.items():
                # Видаляємо цифри з назви команди для пошуку плагіна (open_program1 -> open_program)
                base_command = ''.join(c for c in command_name if not c.isdigit())

                plugin_name = plugin_command_map.get(base_command)
                if plugin_name:
                    if plugin_name not in plugin_commands:
                        plugin_commands[plugin_name] = []
                    plugin_commands[plugin_name].append({
                        "command": base_command,  # Використовуємо базову команду без цифр
                        "params": {"value": param_value}
                    })
                else:
                    logger.warning(f"Command {base_command} (from {command_name}) not found in any plugin")

            # Створюємо execution_plan
            for plugin_name, commands_list in plugin_commands.items():
                execution_plan.append({
                    "plugin": plugin_name,
                    "commands": commands_list
                })

        except Exception as e:
            import traceback
            error_type = type(e).__name__
            error_msg = str(e)

            # Специфічні повідомлення для різних типів помилок
            if "401" in error_msg or "Unauthorized" in error_msg:
                logger.error("OpenAI API authorization failed for command generation", extra={
                    'error': error_msg,
                    'error_type': error_type,
                    'solution': 'Перевірте API ключ OpenAI у config.json'
                })
            elif "timeout" in error_msg.lower() or "TimeoutError" in error_type:
                logger.error("OpenAI API timeout for command generation", extra={
                    'error': error_msg,
                    'error_type': error_type
                })
            else:
                logger.error("Failed to generate plugin commands", extra={
                    'error': error_msg,
                    'error_type': error_type,
                    'traceback': traceback.format_exc()
                    })

        return execution_plan


# Глобальний екземпляр (ініціалізується в main.py)
smart_assistant = None

# Глобальний екземпляр для програм (завжди доступний)
_program_scanner = None

def get_program_mapper():
    """Повертає мапер програм (завжди доступний, навіть без API ключа)"""
    global _program_scanner
    if _program_scanner is None:
        _program_scanner = SmartAssistant('dummy_key_for_scanning_only')
    return _program_scanner

def initialize_smart_assistant(api_key):
    """Ініціалізує ШІ асистента з API ключем"""
    global smart_assistant
    if api_key and api_key != "YOUR_OPENAI_API_KEY_HERE":
        try:
            smart_assistant = SmartAssistant(api_key)
            logger.info("Smart AI assistant initialized successfully", extra={
                'mode': 'AI_enabled',
                'fallback_available': True,
                'programs_found': len(smart_assistant.installed_programs)
            })
            return True
        except Exception as e:
            logger.error("Failed to initialize Smart AI assistant", extra={
                'error': str(e),
                'fallback_mode': 'Available'
            })
            smart_assistant = None
            return False
    else:
        logger.info("OpenAI API key not provided", extra={
            'mode': 'manual_only',
            'fallback_available': True,
            'status': 'System will use manual command recognition'
        })
        return False

def extract_program_name_from_text(text):
    """Розумно виділяє назву програми з тексту команди"""
    text_lower = text.lower().strip()

    # Видаляємо команди-слова
    command_words = ['відкрий', 'запуст', 'включи', 'запуск', 'open', 'launch', 'start', 'run']
    for word in command_words:
        text_lower = text_lower.replace(word, '').strip()

    # Видаляємо допоміжні слова
    helper_words = ['програму', 'додаток', 'application', 'program', 'app']
    for word in helper_words:
        text_lower = text_lower.replace(word, '').strip()

    # Що залишилось - це ймовірно назва програми
    program_name = text_lower.strip()

    return program_name if program_name else "unknown"

def analyze_command_manually(user_text):
    """Резервна система розпізнавання команд без OpenAI API"""
    logger.info("Using manual command analysis", extra={
        'user_text': user_text,
        'mode': 'fallback_manual'
    })

    text_lower = user_text.lower()

    # Пошук ключових слів для визначення типу команди
    program_keywords = ['запуст', 'відкр', 'включ', 'запуск', 'open', 'launch', 'start']
    search_keywords = ['знайд', 'пошук', 'search', 'find', 'ютуб', 'youtube', 'гугл', 'google']
    volume_keywords = ['гучн', 'тих', 'звук', 'volume', 'mute', 'sound']
    test_keywords = ['тест', 'test', 'перевір', 'check']

    # Визначаємо тип команди
    command_type = None
    if any(keyword in text_lower for keyword in test_keywords):
        command_type = "test_search"
    elif any(keyword in text_lower for keyword in program_keywords):
        command_type = "open_app"
    elif any(keyword in text_lower for keyword in search_keywords):
        command_type = "search"
    elif any(keyword in text_lower for keyword in volume_keywords):
        command_type = "volume"

    # Формуємо результат у форматі, схожому на GPT відповідь
    if command_type == "open_app":
        # Розумне виділення назви програми з тексту
        target_program = extract_program_name_from_text(user_text)

        logger.info("Manual analysis: detected program launch", extra={
            'command_type': 'open_app',
            'target_program': target_program or "unknown",
            'confidence': 0.7
        })

        return {
            "success": True,
            "plugins": ["windows_programs"],
            "manual_analysis": True,
            "details": {
                "action": "open_app",
                "target": target_program or "unknown",
                "confidence": 0.7
            }
        }

    elif command_type == "search":
        search_target = "youtube" if any(word in text_lower for word in ['ютуб', 'youtube']) else "google"
        query = user_text  # Використовуємо весь текст як запит

        logger.info("Manual analysis: detected search", extra={
            'command_type': 'search',
            'platform': search_target,
            'confidence': 0.8
        })

        return {
            "success": True,
            "plugins": ["browser_search"],
            "manual_analysis": True,
            "details": {
                "action": "search",
                "platform": search_target,
                "query": query,
                "confidence": 0.8
            }
        }

    elif command_type == "volume":
        volume_action = "down" if any(word in text_lower for word in ['тих', 'меньш']) else "up"

        logger.info("Manual analysis: detected volume control", extra={
            'command_type': 'volume',
            'action': volume_action,
            'confidence': 0.8
        })

        return {
            "success": True,
            "plugins": ["system_control"],
            "manual_analysis": True,
            "details": {
                "action": "volume",
                "type": volume_action,
                "value": 20,
                "confidence": 0.8
            }
        }

    elif command_type == "test_search":
        test_query = extract_program_name_from_text(user_text.replace('тест', '').replace('test', '').replace('перевір', ''))

        logger.info("Manual analysis: detected test search", extra={
            'command_type': 'test_search',
            'query': test_query,
            'confidence': 0.9
        })

        return {
            "success": True,
            "plugins": ["windows_programs"],
            "manual_analysis": True,
            "details": {
                "action": "test_search",
                "query": test_query or "telegram",
                "confidence": 0.9
            }
        }

    logger.warning("Manual analysis: command not recognized", extra={
        'user_text': user_text,
        'detected_keywords': [kw for kw in ['запуст', 'відкр', 'включ', 'знайд', 'пошук', 'гучн', 'тих', 'звук', 'тест'] if kw in text_lower]
    })

    return {
        "success": False,
        "manual_analysis": True,
        "error": "Не вдалося розпізнати команду"
    }

async def execute_manual_command(user_text, manual_analysis):
    """Виконує команду в ручному режимі без GPT"""
    try:
        from smart_plugin_manager import SmartPluginManager

        # Ініціалізуємо менеджер плагінів
        plugin_manager = SmartPluginManager()

        selected_plugins = manual_analysis.get("plugins", [])
        details = manual_analysis.get("details", {})

        logger.info("Executing manual command", extra={
            'user_text': user_text,
            'plugins': selected_plugins,
            'action': details.get('action')
        })

        execution_results = []

        for plugin_name in selected_plugins:
            if plugin_name == "windows_programs" and details.get("action") == "open_app":
                # Виконуємо пошук і запуск програми
                target = details.get("target", "unknown")

                # Спочатку шукаємо програму
                search_result = await plugin_manager.execute_plugin_command(
                    "windows_programs", "search_programs", query=target
                )
                execution_results.append({
                    "plugin": plugin_name,
                    "command": "search_programs",
                    "result": search_result
                })

                # Потім запускаємо, якщо знайшли
                if search_result.get("success"):
                    open_result = await plugin_manager.execute_plugin_command(
                        "windows_programs", "open_program", program_name=target
                    )
                    execution_results.append({
                        "plugin": plugin_name,
                        "command": "open_program",
                        "result": open_result
                    })

            elif plugin_name == "browser_search" and details.get("action") == "search":
                # Виконуємо пошук
                platform = details.get("platform", "google")
                query = details.get("query", user_text)

                command = "search_youtube" if platform == "youtube" else "search_web"

                search_result = await plugin_manager.execute_plugin_command(
                    "browser_search", command, query=query
                )
                execution_results.append({
                    "plugin": plugin_name,
                    "command": command,
                    "result": search_result
                })

            elif plugin_name == "system_control" and details.get("action") == "volume":
                # Керуємо звуком
                volume_type = details.get("type", "up")
                value = details.get("value", 20)

                command = "volume_up" if volume_type == "up" else "volume_down"

                volume_result = await plugin_manager.execute_plugin_command(
                    "system_control", command, step=value
                )
                execution_results.append({
                    "plugin": plugin_name,
                    "command": command,
                    "result": volume_result
                })

            elif plugin_name == "windows_programs" and details.get("action") == "test_search":
                # Тестуємо пошук
                query = details.get("query", "telegram")

                test_result = await plugin_manager.execute_plugin_command(
                    "windows_programs", "test_search", query=query
                )
                execution_results.append({
                    "plugin": plugin_name,
                    "command": "test_search",
                    "result": test_result
                })

        # Аналізуємо результати
        successful_commands = [r for r in execution_results if r["result"].get("success")]

        if successful_commands:
            success_messages = [r["result"].get("message", "OK") for r in successful_commands]
            message = "; ".join(success_messages)

            return {
                "success": True,
                "action": {
                    "type": "manual_execution",
                    "results": execution_results,
                    "successful_count": len(successful_commands),
                    "total_count": len(execution_results)
                },
                "message": message
            }
        else:
            return {
                "success": False,
                "message": "Команду не вдалося виконати в ручному режимі",
                "fallback": True
            }

    except Exception as e:
        logger.error("Manual command execution failed", extra={
            'error': str(e),
            'error_type': type(e).__name__,
            'user_text': user_text
        })
        return {
            "success": False,
            "message": f"Помилка виконання команди: {str(e)}",
            "fallback": True
        }

async def process_smart_command(user_text):
    """Основна функція для обробки команд через ШІ (2-етапна система) з fallback"""
    if not smart_assistant:
        logger.info("AI assistant not configured, using manual command analysis")
        # Використовуємо резервну систему
        manual_result = analyze_command_manually(user_text)
        if manual_result.get("success"):
            return await execute_manual_command(user_text, manual_result)
        else:
            return {
                "success": False,
                "message": "ШІ асистент не налаштовано і команду не вдалося розпізнати",
                "fallback": True
            }

    try:
        from smart_plugin_manager import SmartPluginManager

        # Ініціалізуємо менеджер плагінів
        if not hasattr(smart_assistant, 'plugin_manager'):
            logger.info("Initializing SmartPluginManager")
            try:
                smart_assistant.plugin_manager = SmartPluginManager()
                logger.info("SmartPluginManager initialized successfully")
            except Exception as e:
                import traceback
                logger.error("Failed to initialize SmartPluginManager", extra={
                    'error': str(e),
                    'traceback': traceback.format_exc()
                })
                return {
                    "success": False,
                    "message": f"Помилка ініціалізації плагінів: {str(e)}",
                    "fallback": True
                }

        # ЕТАП 1: GPT обирає потрібні плагіни
        plugin_selection = await smart_assistant.select_plugins(user_text)

        if not plugin_selection.get("success"):
            # Спробуємо ручний режим
            manual_result = analyze_command_manually(user_text)
            if manual_result.get("success"):
                return await execute_manual_command(user_text, manual_result)
            else:
                return {
                    "success": False,
                    "message": "Не вдалося визначити потрібні плагіни",
                    "fallback": True
                }

        selected_plugins = plugin_selection.get("plugins", [])

        # ЕТАП 2: GPT визначає команди для кожного плагіна
        execution_plan = await smart_assistant.execute_plugin_commands(user_text, selected_plugins)
        logger.info(f"Execution plan: {execution_plan}")

        if not execution_plan:
            return {
                "success": False,
                "message": "Не вдалося створити план виконання",
                "fallback": True
            }

        # ЕТАП 3: Виконуємо команди
        execution_results = []

        for plugin_info in execution_plan:
            plugin_name = plugin_info.get("plugin")
            command_sequence = plugin_info.get("commands", [])
            logger.info(f"Executing plugin: {plugin_name}, commands: {command_sequence}")

            for command_info in command_sequence:
                command_name = command_info.get("command")
                params = command_info.get("params", {})
                logger.info(f"Executing command: {command_name} with params: {params}")

                result = await smart_assistant.plugin_manager.execute_plugin_command(
                    plugin_name, command_name, **params
                )

                execution_results.append({
                    "plugin": plugin_name,
                    "command": command_name,
                    "result": result
                })

                # Якщо команда не вдалася - можемо зупинити виконання або продовжити
                if not result.get("success"):
                    logger.warning(f"Command failed: {plugin_name}.{command_name}")

        # Аналізуємо результати
        successful_commands = [r for r in execution_results if r["result"].get("success")]
        failed_commands = [r for r in execution_results if not r["result"].get("success")]

        if successful_commands:
            success_messages = [r["result"].get("message", "OK") for r in successful_commands]
            message = "; ".join(success_messages)

            return {
                "success": True,
                "action": {
                    "type": "plugin_execution",
                    "results": execution_results,
                    "successful_count": len(successful_commands),
                    "total_count": len(execution_results)
                },
                "message": message
            }
        else:
            return {
                "success": False,
                "message": "Жодна команда не виконалася успішно",
                "fallback": True
            }

    except Exception as e:
        import traceback
        error_type = type(e).__name__
        error_msg = str(e)

        # Покращена обробка помилок з конкретними порадами та fallback
        if "401" in error_msg or "Unauthorized" in error_msg:
            logger.error("OpenAI API authorization failed, trying fallback mode", extra={
                'error': error_msg,
                'error_type': error_type,
                'user_text': user_text,
                'solution': 'Перевірте openaiApiKey у config.json'
            })
            # Спробуємо fallback режим
            manual_result = analyze_command_manually(user_text)
            if manual_result.get("success"):
                logger.info("Using fallback manual command analysis due to API error")
                return await execute_manual_command(user_text, manual_result)
            else:
                user_message = "Помилка авторизації OpenAI API і команду не вдалося розпізнати автоматично"

        elif "timeout" in error_msg.lower() or "TimeoutError" in error_type:
            logger.error("OpenAI API timeout, trying fallback mode", extra={
                'error': error_msg,
                'error_type': error_type,
                'user_text': user_text
            })
            # Спробуємо fallback режим
            manual_result = analyze_command_manually(user_text)
            if manual_result.get("success"):
                logger.info("Using fallback manual command analysis due to timeout")
                return await execute_manual_command(user_text, manual_result)
            else:
                user_message = "Таймаут з'єднання з OpenAI API і команду не вдалося розпізнати автоматично"

        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            logger.error("Network error, trying fallback mode", extra={
                'error': error_msg,
                'error_type': error_type,
                'user_text': user_text
            })
            # Спробуємо fallback режим
            manual_result = analyze_command_manually(user_text)
            if manual_result.get("success"):
                logger.info("Using fallback manual command analysis due to network error")
                return await execute_manual_command(user_text, manual_result)
            else:
                user_message = "Проблеми з мережею і команду не вдалося розпізнати автоматично"

        elif "SmartPluginManager" in error_msg:
            user_message = "Помилка завантаження плагінів системи."
            logger.error("Plugin system initialization failed", extra={
                'error': error_msg,
                'error_type': error_type,
                'user_text': user_text,
                'traceback': traceback.format_exc()
            })
        else:
            user_message = f"Загальна помилка ШІ асистента: {error_msg}"
            logger.error("Smart command processing failed", extra={
                'error': error_msg,
                'error_type': error_type,
                'user_text': user_text,
                'traceback': traceback.format_exc()
            })

        return {
            "success": False,
            "message": user_message,
            "fallback": True
        }