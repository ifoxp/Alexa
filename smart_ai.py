import json
import asyncio
from datetime import datetime
from openai import AsyncOpenAI
from logger_config import get_logger
from audio_player import speak_text

logger = get_logger('smart_ai')

class SmartAssistant:
    def __init__(self, api_key, model="gpt-4o-mini"):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.plugin_manager = None

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

ВАЖЛИВО: Спочатку визнач - це КОМАНДА чи просто РОЗМОВА?

КОМАНДИ (потребують виконання):
- "відкрий Steam"
- "знайди котиків на ютубі"
- "зроби звук тихіше"
- "запусти телеграм"

НЕ КОМАНДИ (звичайна розмова):
- "прикольна відкрив мені Steam"
- "класно, спасибо"
- "це що, круто"
- "ну даже покруче"
- "зрозумів проблему?"

Якщо це НЕ команда - поверни {{"isCommand": false}}
Якщо це команда - поверни плагіни для виконання.

ФОРМАТ ВІДПОВІДІ (тільки JSON):
{{"isCommand": true, "success": true, "plugins": ["назва_плагіна1"], "confidence": 0.95}}
АБО
{{"isCommand": false}}

ПРИКЛАДИ:
"запусти телеграм" → {{"isCommand": true, "success": true, "plugins": ["windows_programs"], "confidence": 0.95}}
"знайди котиків на ютубі" → {{"isCommand": true, "success": true, "plugins": ["browser_search"], "confidence": 0.90}}
"прикольна відкрив мені Steam" → {{"isCommand": false}}
"класно, спасибо" → {{"isCommand": false}}"""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a smart assistant that analyzes user commands and selects appropriate plugins."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )

            result_text = response.choices[0].message.content.strip()
            logger.info(f"GPT plugin selection result: {result_text}")

            if not result_text:
                return {"success": False, "error": "Empty response from GPT"}

            try:
                result = json.loads(result_text)

                # Перевіряємо чи це команда взагалі
                is_command = result.get("isCommand", True)  # За замовчуванням вважаємо командою (для сумісності)

                if not is_command:
                    logger.info("Detected casual talk, not a command")
                    return {"success": False, "error": "Not a command", "casual_talk": True}

                # Якщо це команда - обробляємо як раніше
                plugin_names = result.get("plugins", [])
                logger.info(f"Parsed plugin names: {plugin_names}")

                if plugin_names:
                    return {"success": True, "plugins": plugin_names}

                return {"success": False, "error": "No valid plugins selected"}
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}, GPT response was: {result_text}")
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
                user_friendly_msg = "OpenAI повернув пусту відповідь"
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

        prompt = f"""Команда користувача: "{user_text}"

Доступні команди:
{commands_text}

Проаналізуй команду і поверни JSON з потрібними командами + природною відповіддю для озвучування.

ВАЖЛИВО:
- Використовуй ТОЧНО ті програми що згадав користувач
- Не додавай програми які користувач не просив
- Якщо користувач каже "Steam discord", то тільки Steam та Discord
- Додай природну відповідь українською як справжній Джарвіс

ДЛЯ МНОЖИННИХ ПРОГРАМ використовуй нумеровані ключі:

Приклади:
"запусти Steam і зроби звук на 77%" -> {{
  "commands": {{"open_program": "Steam", "set_volume": "77"}},
  "response": "Добре, запускаю Steam і встановлюю гучність на 77 відсотків"
}}

"відкрий Steam discord" -> {{
  "commands": {{"open_program1": "Steam", "open_program2": "Discord"}},
  "response": "Окей, відкриваю Steam і Discord для вас"
}}

"знайди котиків на youtube" -> {{
  "commands": {{"search_youtube": "котики"}},
  "response": "Шукаю котиків на YouTube"
}}

"зроби тихіше на 20" -> {{
  "commands": {{"volume_down": "20"}},
  "response": "Зменшую гучність на 20 відсотків"
}}

Формат відповіді: {{"commands": {{"команда1": "параметр1"}}, "response": "природна відповідь українською"}}"""

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

            parsed_result = json.loads(result_text)

            # Отримуємо команди і відповідь від GPT
            commands_dict = parsed_result.get("commands", {})
            natural_response = parsed_result.get("response", "")

            logger.info(f"Natural response from AI: '{natural_response}'")

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

            # Створюємо execution_plan з природною відповіддю
            for plugin_name, commands_list in plugin_commands.items():
                execution_plan.append({
                    "plugin": plugin_name,
                    "commands": commands_list,
                    "natural_response": natural_response  # Додаємо природну відповідь
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


def initialize_smart_assistant(api_key):
    """Ініціалізує ШІ асистента з API ключем"""
    global smart_assistant
    if api_key and api_key != "YOUR_OPENAI_API_KEY_HERE":
        try:
            smart_assistant = SmartAssistant(api_key)
            logger.info("Smart AI assistant initialized successfully", extra={
                'mode': 'AI_enabled'
            })
            return True
        except Exception as e:
            logger.error("Failed to initialize Smart AI assistant", extra={
                'error': str(e)
            })
            smart_assistant = None
            return False
    else:
        logger.info("OpenAI API key not provided", extra={
            'mode': 'no_ai',
            'status': 'AI assistant will not be available'
        })
        return False



async def process_smart_command(user_text):
    """Основна функція для обробки команд через ШІ (2-етапна система)"""
    if not smart_assistant:
        logger.error("AI assistant not configured")
        return {
            "success": False,
            "message": "ШІ асистент не налаштовано. Перевірте API ключ у config.json"
        }

    try:
        from smart_plugin_manager import SmartPluginManager

        # Ініціалізуємо менеджер плагінів
        if not hasattr(smart_assistant, 'plugin_manager') or smart_assistant.plugin_manager is None:
            logger.info("Initializing SmartPluginManager")
            smart_assistant.plugin_manager = SmartPluginManager()
            logger.info("SmartPluginManager initialized successfully")

        # ЕТАП 1: GPT обирає потрібні плагіни
        plugin_selection = await smart_assistant.select_plugins(user_text)
        logger.info(f"Plugin selection result: {plugin_selection}")

        if not plugin_selection.get("success"):
            # Перевіряємо чи це звичайна розмова
            if plugin_selection.get("casual_talk"):
                logger.info("User is having casual talk, not executing commands")
                return {
                    "success": False,
                    "message": "Розмова розпізнана, команда не виконується",
                    "casual_talk": True
                }

            logger.warning(f"Plugin selection failed: {plugin_selection}")
            return {
                "success": False,
                "message": "Не вдалося визначити потрібні плагіни"
            }

        selected_plugins = plugin_selection.get("plugins", [])

        # ЕТАП 2: GPT визначає команди для кожного плагіна
        execution_plan = await smart_assistant.execute_plugin_commands(user_text, selected_plugins)
        logger.info(f"Execution plan: {execution_plan}")

        if not execution_plan:
            return {
                "success": False,
                "message": "Не вдалося створити план виконання"
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

                if not result.get("success"):
                    logger.warning(f"Command failed: {plugin_name}.{command_name}")

        # Аналізуємо результати
        successful_commands = [r for r in execution_results if r["result"].get("success")]

        if successful_commands:
            # Використовуємо природну відповідь від AI замість технічних повідомлень
            natural_response = ""

            # Шукаємо природну відповідь в execution_plan
            for plugin_info in execution_plan:
                if plugin_info.get("natural_response"):
                    natural_response = plugin_info.get("natural_response")
                    break

            # Якщо немає природної відповіді, використовуємо технічні повідомлення
            if not natural_response:
                success_messages = [r["result"].get("message", "OK") for r in successful_commands]
                final_message = "; ".join(success_messages)
            else:
                final_message = natural_response
                logger.info(f"Using natural AI response: {natural_response}")

            # Голосова відповідь при успішному виконанні
            try:
                import config_manager as cfg
                config = cfg.load_config()
                speak_text(final_message, config)
            except Exception as tts_error:
                logger.debug(f"TTS error: {tts_error}")

            return {
                "success": True,
                "action": {
                    "type": "plugin_execution",
                    "results": execution_results,
                    "successful_count": len(successful_commands),
                    "total_count": len(execution_results)
                },
                "message": final_message
            }
        else:
            final_message = "Жодна команда не виконалася успішно"

            # Голосова відповідь при неуспішному виконанні
            try:
                import config_manager as cfg
                config = cfg.load_config()
                speak_text("Команду не вдалося виконати", config)
            except Exception as tts_error:
                logger.debug(f"TTS error: {tts_error}")

            return {
                "success": False,
                "message": final_message
            }

    except Exception as e:
        import traceback
        error_type = type(e).__name__
        error_msg = str(e)

        # Конкретні повідомлення про помилки
        if "401" in error_msg or "Unauthorized" in error_msg:
            user_message = "Помилка авторизації OpenAI API. Перевірте API ключ у config.json"
        elif "timeout" in error_msg.lower() or "TimeoutError" in error_type:
            user_message = "Таймаут з'єднання з OpenAI API"
        elif "network" in error_msg.lower() or "connection" in error_msg.lower():
            user_message = "Проблеми з підключенням до OpenAI API"
        elif "SmartPluginManager" in error_msg:
            user_message = "Помилка завантаження плагінів системи"
        else:
            user_message = f"Помилка ШІ асистента: {error_msg}"

        logger.error("Smart command processing failed", extra={
            'error': error_msg,
            'error_type': error_type,
            'user_text': user_text,
            'traceback': traceback.format_exc()
        })

        return {
            "success": False,
            "message": user_message
        }