import json
import asyncio
from datetime import datetime
from openai import AsyncOpenAI
from logger_config import get_logger
from audio_player import speak_text

logger = get_logger('smart_ai')

class SmartAssistant:
    def __init__(self, api_key, model="gpt-4o-mini"):
        self.client = AsyncOpenAI(
            api_key=api_key,
            timeout=15.0,  # Глобальний таймаут для всіх запитів
            max_retries=2   # Максимум 2 спроби
        )
        self.model = model
        self.plugin_manager = None
        # Контекст для Jarvis-стилю
        self.conversation_history = []  # Останні 2 фрази користувача
        self.last_responses = []  # Останні 2 відповіді Jarvis
        self.used_greetings = set()  # Щоб не повторювати одні й ті самі звертання
        # Кеш для швидких відповідей (простий лру кеш)
        self.response_cache = {}
        self.max_cache_size = 20

    def update_conversation_context(self, user_text: str, jarvis_response: str):
        """Оновлює контекст розмови для Jarvis-стилю"""
        # Додаємо нову фразу, зберігаємо тільки останні 2
        self.conversation_history.append(user_text)
        if len(self.conversation_history) > 2:
            self.conversation_history.pop(0)

        self.last_responses.append(jarvis_response)
        if len(self.last_responses) > 2:
            self.last_responses.pop(0)

    async def generate_jarvis_response_parallel(self, user_text: str, selected_plugins: list):
        """ОНОВЛЕНИЙ МЕТОД: Генерує команди + Jarvis відповідь в одному запиті"""

        # Тепер execute_plugin_commands повертає і команди, і jarvis відповідь
        execution_plan, jarvis_response = await self.execute_plugin_commands(user_text, selected_plugins)

        return jarvis_response, execution_plan

    async def select_plugins(self, user_text: str):
        """ЕТАП 1: GPT обирає потрібні плагіни для обробки команди."""
        try:
            plugins_summary = self.plugin_manager.get_plugins_summary()

            plugins_list = []
            for i, plugin in enumerate(plugins_summary, 1):
                try:
                    plugin_desc = plugin['name'] + ' - ' + plugin.get('description', '')  # Додаємо '' для уникнення KeyError, якщо 'description' відсутній
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

            # ОПТИМІЗАЦІЇ ШВИДКОСТІ GPT
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a smart assistant that analyzes user commands and selects appropriate plugins."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.1,  # Низька температура для детермінованості
                top_p=0.9,        # Обмежуємо вибір токенів
                frequency_penalty=0,
                presence_penalty=0,
                timeout=10        # Таймаут 10 секунд
            )

            result_text = response.choices[0].message.content.strip()
            print(f"GPT plugin selection result: {result_text}")

            if not result_text:
                return {"success": False, "error": "Empty response from GPT"}

            try:
                result = json.loads(result_text)

                # Перевіряємо чи це команда взагалі
                is_command = result.get("isCommand", True)  # За замовчуванням вважаємо командою (для сумісності)

                if not is_command:
                    return {"success": False, "error": "Not a command", "casual_talk": True}

                # Якщо це команда - обробляємо як раніше
                plugin_names = result.get("plugins", [])

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

        # Додаємо контекст попередніх команд
        context_text = ""
        if self.conversation_history:
            context_text = f"\nПопередні команди користувача: {' | '.join(self.conversation_history)}"

        # Додаємо інформацію про попередні відповіді Jarvis
        if self.last_responses:
            context_text += f"\nТвої попередні відповіді: {' | '.join(self.last_responses)}"

        # Формуємо системний промпт (правила для JARVIS)
        system_prompt = """Ти — JARVIS, високоінтелектуальний штучний інтелект. 
Твоя задача: перетворити запит користувача на команди для системи та згенерувати коротку відповідь.

ХАРАКТЕР ТА ТОН:
- ЗАВЖДИ звертайся до користувача "сер".
- Твій стиль: британський дворецький — елегантний, ввічливий, професійний.
- ВАЖЛИВО: Твої відповіді мають бути ЖИВИМИ та РІЗНОМАНІТНИМИ. Аналізуй "Попередні відповіді" і НІКОЛИ не повторюй ту саму фразу.
- Адаптуй відповідь під дію: якщо відкриваєш гру (GTA, Cyberpunk) — побажай приємного відпочинку; якщо відкриваєш IDE чи робочі програми — побажай продуктивної роботи.

ПРАВИЛА ПАРАМЕТРІВ:
- Гучність: "трішки тише" (~10-15%), "значно тише" (~30-50%).
- Програми: витягуй точну офіційну назву ("стім" → "Steam").
- Пошук: залишай лише ключові слова.
- Якщо кілька програм: використовуй ключі open_program1, open_program2.

ФОРМАТ ВІДПОВІДІ (строго JSON):
{
  "commands": {"назва_команди": "значення_параметра"},
  "jarvis_response": "Твоя унікальна, жива відповідь на 4-10 слів, що закінчується на 'сер'."
}"""

        # Формуємо користувацький промпт (поточна ситуація)
        user_prompt = f"""Користувач каже: "{user_text}"

Доступні команди:
{commands_text}
{context_text}

Проаналізуй запит, обери команди та згенеруй відповідь у форматі JSON."""

        try:
            # ОПТИМІЗАЦІЇ ШВИДКОСТІ GPT
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}, # Гарантує валідний JSON
                max_tokens=250,
                temperature=0.7,  # Піднято з 0.2! Це дасть варіативність фраз
                top_p=0.9,
                frequency_penalty=0.5, # Штраф за повторення слів (робить мову багатшою)
                presence_penalty=0.2,
                timeout=12
            )

            result_text = response.choices[0].message.content.strip()
            print(f"Stage 2 AI response: '{result_text}'")

            # Тепер результат містить команди + jarvis відповідь
            parsed_result = json.loads(result_text)
            commands_dict = parsed_result.get("commands", {})
            jarvis_response = parsed_result.get("jarvis_response", "Так, сер")

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

            # Створюємо execution_plan без природної відповіді
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

        return execution_plan, jarvis_response if 'jarvis_response' in locals() else "Помилка, сер"


# Глобальний екземпляр (ініціалізується в main.py)
smart_assistant = None


def initialize_smart_assistant(api_key):
    """Ініціалізує ШІ асистента з API ключем"""
    global smart_assistant
    if api_key and api_key != "YOUR_OPENAI_API_KEY_HERE":
        try:
            smart_assistant = SmartAssistant(api_key)
            logger.info("Smart AI assistant initialized successfully")
            return True
        except Exception as e:
            logger.error("Failed to initialize Smart AI assistant", extra={
                'error': str(e)
            })
            smart_assistant = None
            return False
    else:
        logger.info("OpenAI API key not provided - AI assistant will not be available")
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
                smart_assistant.plugin_manager = SmartPluginManager()

        # ЕТАП 1: GPT обирає потрібні плагіни
        plugin_selection = await smart_assistant.select_plugins(user_text)

        if not plugin_selection.get("success"):
            # Перевіряємо чи це звичайна розмова
            if plugin_selection.get("casual_talk"):
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

        # НОВИЙ ПІДХІД: Паралельно генеруємо швидку відповідь та команди
        quick_response, execution_plan = await smart_assistant.generate_jarvis_response_parallel(
            user_text, selected_plugins
        )

        # ГОТУЄМО відповідь заздалегідь але НЕ озвучуємо до успішного виконання
        print(f"Quick Jarvis response prepared: {quick_response}")

        # Завантажуємо конфігурацію для TTS
        try:
            import config_manager as cfg
            config = cfg.load_config()
        except Exception as config_error:
            print(f"Config load error: {config_error}")
            config = {}

        # Перевіряємо чи вдалося створити план виконання
        if isinstance(execution_plan, Exception) or not execution_plan:
            logger.warning(f"Execution plan failed: {execution_plan}")
            return {
                "success": False,
                "message": "Не вдалося створити план виконання",
                "quick_response": quick_response
            }

        # ЕТАП 3: Виконуємо команди
        execution_results = []

        for plugin_info in execution_plan:
            plugin_name = plugin_info.get("plugin")
            command_sequence = plugin_info.get("commands", [])

            for command_info in command_sequence:
                command_name = command_info.get("command")
                params = command_info.get("params", {})

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
            # Оновлюємо контекст розмови для наступних запитів
            smart_assistant.update_conversation_context(user_text, quick_response)

            # ТЕПЕР озвучуємо готову відповідь після успішного виконання
            print(f"Command successful - playing Jarvis response: {quick_response}")
            tts_task = None
            try:
                # НЕГАЙНО запускаємо TTS з готовою відповіддю
                tts_task = asyncio.create_task(asyncio.to_thread(speak_text, quick_response, config))
            except Exception as tts_error:
                print(f"Success TTS error: {tts_error}")

            # Формуємо фінальну відповідь
            final_message = f"Команда виконана"

            # Чекаємо завершення TTS перед поверненням (уникаємо самопрослуховування)
            if tts_task and not tts_task.done():
                try:
                    await tts_task
                    # Невелика пауза після завершення TTS
                    await asyncio.sleep(0.5)
                except Exception:
                    pass

            return {
                "success": True,
                "action": {
                    "type": "plugin_execution",
                    "results": execution_results,
                    "successful_count": len(successful_commands),
                    "total_count": len(execution_results)
                },
                "message": final_message,
                "quick_response": quick_response  # Повертаємо швидку відповідь для логування
            }
        else:
            final_message = "Жодна команда не виконалася успішно"

            # Голосова відповідь при неуспішному виконанні (використовуємо вже завантажений config)
            print(f"Command failed - playing error message")
            try:
                speak_text("Вибачте, команду не вдалося виконати, сер", config)
            except Exception as tts_error:
                print(f"Error TTS failed: {tts_error}")

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