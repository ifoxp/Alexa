import json
import asyncio
from datetime import datetime
from openai import AsyncOpenAI
from logger_config import get_logger
from audio_player import speak_text
from command_logger import command_logger

logger = get_logger('smart_ai')

class SmartAssistant:
    def __init__(self, api_key, model="gpt-4.1-mini"): 
        self.client = AsyncOpenAI(
            api_key=api_key,
            timeout=15.0,
            max_retries=2
        )
        self.model = model
        self.plugin_manager = None
        self.conversation_history = []
        self.last_responses = []
        self.last_active_plugins = [] # Пам'ять для контексту
        self.used_greetings = set()
        # Кеш для швидких відповідей (простий лру кеш)
        self.response_cache = {}
        self.max_cache_size = 20

    def update_conversation_context(self, user_text: str, jarvis_response: str, executed_plugins: list = None):
        """Оновлює контекст розмови для Jarvis-стилю"""
        # Зберігаємо історію фраз
        self.conversation_history.append(user_text)
        if len(self.conversation_history) > 2:
            self.conversation_history.pop(0)

        self.last_responses.append(jarvis_response)
        if len(self.last_responses) > 2:
            self.last_responses.pop(0)
            
        # ОНОВЛЮЄМО ПАМ'ЯТЬ ПЛАГІНІВ (Важливо для 'зроби тихіше')
        if executed_plugins:
            self.last_active_plugins = executed_plugins
            logger.info(f"Context updated with plugins: {executed_plugins}")
        

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
           
            # Додаємо контекст у тому ж форматі що і в execute_plugin_commands
            context_hint = ""
            if len(self.conversation_history) >= 1 and len(self.last_responses) >= 1:
                # Останні 2 записи у форматі "користувач сказав; ... Jarvis відповів: ..."
                conversations = []
                for i in range(min(len(self.conversation_history), len(self.last_responses), 2)):
                    idx = -(i + 1)  # Починаємо з останнього елемента
                    user_said = self.conversation_history[idx]
                    jarvis_replied = self.last_responses[idx]
                    conversations.insert(0, f"користувач сказав; {user_said}\nJarvis відповів: {jarvis_replied}")

                # Додаємо інформацію про плагіни до останнього запису контексту
                if getattr(self, 'last_active_plugins', None):
                    last_conversation = conversations[-1]  # Останній запис
                    last_conversation += f"\nВикористані плагіни: {self.last_active_plugins}"
                    conversations[-1] = last_conversation

                context_hint = f"\nКОНТЕКСТ ПОПЕРЕДНЬОЇ ДІЇ:\n" + "\n".join(conversations)
                context_hint += f"\n\nЯК ПРАЦЮВАТИ З КОНТЕКСТОМ:\n1. Якщо користувач просить продовжити ту саму дію (наприклад, 'тихіше', 'гучніше', 'ще', 'наступний') — ОБОВ'ЯЗКОВО поверни ті ж самі плагіни.\n2. Якщо користувач продовжує говорити про ТОЙ САМИЙ об'єкт (наприклад, про Samsung), але хоче зробити ІНШУ дію (наприклад, замість новин тепер хоче дізнатися, де купити) — обери НОВИЙ плагін, який підходить для цієї нової дії (наприклад, browser_search)."

            prompt = f"""Ти — ядро маршрутизації голосового асистента. Твоє завдання — проаналізувати репліку і вирішити, чи це цільовий запит до тебе (команда), чи просто фонова розмова.

Користувач каже: "{user_text}"
Попредні відповіді для контексту:
{context_hint}

ДОСТУПНІ ПЛАГІНИ ТА ЇХНІ ОПИСИ:
{plugins_text}

ЛОГІКА ПРИЙНЯТТЯ РІШЕНЬ (Уважно читай кожне правило):
1. ВИЗНАЧЕННЯ КОМАНДИ: Команда — це БУДЬ-ЯКИЙ запит, який вимагає від тебе дії: пошуку інформації, читання новин, запуску програм, перевірки графіків або створення нотаток. Навіть якщо це звучить як просте питання ("які новини?", "що по графіку?", "знайди фільм") — ЦЕ КОМАНДА.
2. ЗВЕРНЕННЯ ДО АСИСТЕНТА: Якщо репліка містить наказовий спосіб ("розкажи", "покажи", "знайди", "запусти") або пряме запитання, яке відповідає функціоналу плагінів — вважай, що звертаються саме до тебе.
3. ЗІСТАВЛЕННЯ: Проаналізуй намір користувача та описи плагінів. Якщо запит користувача можна виконати за допомогою ХОЧА Б ОДНОГО з перелічених плагінів — це 100% КОМАНДА (isCommand: true) і ти маєш вказати цей плагін.
4. ЗВИЧАЙНА РОЗМОВА: Це ЛИШЕ ті випадки, коли користувач просто спілкується ("привіт", "як справи", "круто", "дякую"), розмовляє з кимось іншим у кімнаті, або його репліка взагалі не стосується жодного з доступних плагінів. Тільки тоді isCommand: false.

ФОРМАТ ВІДПОВІДІ (строго JSON, жодного іншого тексту):
{{
  "reasoning": "Тут коротко поясни крок за кроком, що хоче користувач і до якого плагіна це належить",
  "isCommand": true_або_false,
  "plugins": ["назва_плагіна_з_переліку_якщо_є"],
  "confidence": 0.95
}}

Увага:
- Обирай плагіни ТІЛЬКИ з наданого списку.
- Якщо isCommand = false, масив plugins має бути порожнім [].
"""

            # ОПТИМІЗОВАНИЙ ВИКЛИК ЕТАПУ 1
            response = await self.client.chat.completions.create(
                model="gpt-4.1-nano", 
                messages=[
                    {"role": "system", "content": "You are a smart command router. You must always respond in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=200, # Параметр для 4.1 серії
                temperature=0.4,
                timeout=10
            )
            print(f"Available plugins for selection:\n{prompt}")
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

        # Додаємо контекст у новому форматі: "користувач сказав; ... Jarvis відповів: ..."
        context_text = ""
        if len(self.conversation_history) >= 1 and len(self.last_responses) >= 1:
            # Останні 2 записи
            conversations = []
            for i in range(min(len(self.conversation_history), len(self.last_responses), 2)):
                idx = -(i + 1)  # Починаємо з останнього елемента
                user_said = self.conversation_history[idx]
                jarvis_replied = self.last_responses[idx]
                conversations.insert(0, f"користувач сказав; {user_said}\nJarvis відповів: {jarvis_replied}")

            context_text = f"\nПопередній контекст:\n" + "\n".join(conversations)
            context_text += f"\n\nЯК ПРАЦЮВАТИ З КОНТЕКСТОМ:\n1. Якщо користувач просить продовжити ту саму дію (наприклад, 'тихіше', 'гучніше', 'ще', 'наступний') — ОБОВ'ЯЗКОВО поверни ті ж самі плагіни.\n2. Якщо користувач продовжує говорити про ТОЙ САМИЙ об'єкт (наприклад, про Samsung), але хоче зробити ІНШУ дію (наприклад, замість новин тепер хоче дізнатися, де купити) — обери НОВИЙ плагін, який підходить для цієї нової дії."
        # Формуємо системний промпт (правила для JARVIS)
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

СУВОРА ЗАБОРОНА:
Ключ 'commands' має бути ПЛОСКИМ об'єктом. Тобі СУВОРО ЗАБОРОНЕНО вигадувати свої назви команд. Ти ПОВИНЕН брати точні назви команд ЛИШЕ з наданого списку. Наприклад, якщо треба увімкнути виконавця, використовуй саме ту команду, яка для цього вказана в списку, а не вигадуй 'play_artist'.

ФОРМАТ ВІДПОВІДІ (строго JSON):
{
  "thought_process": "Коротко проаналізуй, що треба зробити і ЯКУ ТОЧНО команду зі списку ти обереш.",
  "commands": {"точна_назва_команди_зі_списку": "значення_параметра"},
  "jarvis_response": "Твоя унікальна, жива відповідь на 4-10 слів, що закінчується на 'сер'."
}"""

        # Формуємо користувацький промпт (поточна ситуація)
        user_prompt = f"""Користувач каже: "{user_text}"

{context_text}

Доступні команди:
{commands_text}

Проаналізуй запит, обери команди та згенеруй відповідь у форматі JSON."""
        print(f"Executing plugin commands with prompt:\n{user_prompt}")
        try:
            # ОПТИМІЗАЦІЯ ДЛЯ ЕТАПУ 2 (GPT-5 NANO)
            # ОПТИМІЗАЦІЯ ДЛЯ ЕТАПУ 2 (GPT-4.1 NANO)
            response = await self.client.chat.completions.create(
                model="gpt-4.1-nano", 
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=400,
                temperature=0.3, # ЗНИЖЕНО ДЛЯ СТАБІЛЬНОСТІ
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
                # Видаляємо цифрові суфікси з назви команди для пошуку плагіна (open_program1 -> open_program, set_specific_app_volume_2 -> set_specific_app_volume)
                import re
                base_command = re.sub(r'_?\d+$', '', command_name)

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

        # Логуємо навіть якщо ШІ не налаштований
        try:
            await command_logger.log_command(user_text, "ШІ асистент не налаштовано", "Етап 2 не досягнуто")
        except:
            pass

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

        # Логуємо етап 1 (завжди)
        stage1_response = str(plugin_selection)

        if not plugin_selection.get("success"):
            # Логуємо неуспішну команду
            await command_logger.log_command(user_text, stage1_response, "Команда не виконана - етап 2 не досягнуто")

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

        # Логуємо етап 2
        stage2_response = f"Jarvis response: {quick_response} | Execution plan: {execution_plan}"

        # Зберігаємо в лог файл
        await command_logger.log_command(user_text, stage1_response, stage2_response)

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
            # Оновлюємо контекст розмови ТА ПЕРЕДАЄМО ПЛАГІНИ
            smart_assistant.update_conversation_context(user_text, quick_response, selected_plugins)

            # Перевіряємо, чи плагін має власний текст для озвучування
            plugin_speak_text = None
            for result in successful_commands:
                plugin_result = result.get("result", {})
                if "speak_text" in plugin_result:
                    plugin_speak_text = plugin_result["speak_text"]
                    break

            # Вибираємо що озвучувати: відповідь плагіна або стандартну відповідь Jarvis
            text_to_speak = plugin_speak_text if plugin_speak_text else quick_response

            print(f"Command successful - playing response: {text_to_speak}")
            tts_task = None
            try:
                # Запускаємо TTS з обраним текстом
                tts_task = asyncio.create_task(asyncio.to_thread(speak_text, text_to_speak, config))
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

        # Логуємо помилку
        try:
            await command_logger.log_command(user_text, f"ПОМИЛКА: {error_msg}", "Етап 2 не досягнуто через помилку")
        except:
            pass  # Щоб не зациклитися на помилках логування

        return {
            "success": False,
            "message": user_message
        }