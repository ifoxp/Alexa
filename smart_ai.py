import json
import asyncio
import time
from datetime import datetime
from openai import AsyncOpenAI
from logger_config import get_logger
from audio_player import speak_text
from command_logger import command_logger

logger = get_logger('smart_ai')

class SmartAssistant:
    def __init__(self, api_key, model="gemini-2.5-flash-lite"): 
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/", # Перенаправлення на Gemini
            timeout=8.0,
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

    async def process_single_pass(self, user_text: str):
        """ОДНОПРОХІДНИЙ АЛГОРИТМ: Одночасно визначає плагін, команди та генерує відповідь."""
        try:
            # 1. Збираємо абсолютно всі плагіни та їх команди в одне "меню"
            plugins_summary = self.plugin_manager.get_plugins_summary()
            all_capabilities = []
            
            for plugin in plugins_summary:
                plugin_name = plugin['name']
                plugin_desc = plugin.get('description', '')
                
                # Отримуємо команди для цього конкретного плагіна
                plugin_info = self.plugin_manager.get_plugin_commands(plugin_name)
                commands_str = ""
                if plugin_info and 'commands' in plugin_info:
                    cmds = [f"    - {c_name}: {c_desc}" for c_name, c_desc in plugin_info['commands'].items()]
                    commands_str = "\n".join(cmds)
                else:
                    commands_str = "    (немає специфічних команд)"
                    
                all_capabilities.append(f"[{plugin_name}] - {plugin_desc}\n  Доступні команди:\n{commands_str}")
                
            capabilities_text = "\n\n".join(all_capabilities)

            # 2. Формуємо контекст попередніх розмов
            context_hint = ""
            if len(self.conversation_history) >= 1 and len(self.last_responses) >= 1:
                conversations = []
                for i in range(min(len(self.conversation_history), len(self.last_responses), 2)):
                    idx = -(i + 1)
                    user_said = self.conversation_history[idx]
                    jarvis_replied = self.last_responses[idx]
                    conversations.insert(0, f"користувач сказав; {user_said}\nJarvis відповів: {jarvis_replied}")

                if getattr(self, 'last_active_plugins', None):
                    last_conversation = conversations[-1]
                    last_conversation += f"\nВикористані плагіни: {self.last_active_plugins}"
                    conversations[-1] = last_conversation

                context_hint = f"\nКОНТЕКСТ ПОПЕРЕДНЬОЇ ДІЇ:\n" + "\n".join(conversations)
                context_hint += f"\n\nПРАВИЛО КОНТЕКСТУ: Якщо нова репліка продовжує дію (наприклад, 'тихіше', 'наступний') — використовуй ті ж плагіни. Якщо це нова дія — ігноруй контекст."

            # 3. Єдиний системний промпт, який робить все одразу
            system_prompt = f"""Ти — JARVIS, розумний маршрутизатор та голосовий асистент. 
Твоя задача — за один крок проаналізувати репліку, обрати потрібний плагін, команду і згенерувати живу відповідь.

МЕНЮ ДОСТУПНИХ ПЛАГІНІВ ТА КОМАНД:
{capabilities_text}

АЛГОРИТМ ПРИЙНЯТТЯ РІШЕННЯ:
КРОК 1. АБСОЛЮТНИЙ ПРІОРИТЕТ (ДРУК): Якщо текст містить слова "напиши", "надрукуй", "введи", "набери" — це ЗАВЖДИ плагін `keyboard_typing`. Ігноруй весь подальший текст.
КРОК 2. ПОШУК КОМАНДИ: Якщо це не друк, знайди плагін, опис якого відповідає запиту. Знайди точну назву команди з його списку.
КРОК 3. ЧИСТА РОЗМОВА: Якщо в тексті немає жодної вказівки до дії (просто "привіт", "як справи") — встанови `isCommand: false` і порожній `execution_plan`.

ПРАВИЛА ДЛЯ ВІДПОВІДІ (jarvis_response):
- Відповідь має бути УЛЬТРАКОРОТКОЮ. Максимум 1-3 слова.
- Дозволені варіанти: "Так, сер", "Виконую", "Вже роблю", "Секунду", "Запскаю Steam", "Запускаю програми", "Вмикаю Neffex".
- НІКОЛИ не перераховуй програми чи дії, які ти збираєшся виконати. Економ час.

ФОРМАТ ВІДПОВІДІ (строго JSON):
{{
  "isCommand": true або false,
  "execution_plan": [
    {{
      "plugin": "точна_назва_плагіна",
      "commands": [
        {{
          "command": "точна_назва_команди",
          "params": {{"value": "значення_параметра (наприклад, назва пісні або програми)"}}
        }}
      ]
    }}
  ],
  "jarvis_response": "Твоя ультракоротка відповідь."
}}"""

            user_prompt = f"""Користувач каже: "{user_text}"\n{context_hint}"""
            
            logger.info(f"GPT SINGLE-PASS СИСТЕМНИЙ ПРОМПТ:\n{system_prompt}")

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                max_completion_tokens=400,
                temperature=0.4, # Баланс між точністю роутингу (0.1) та живою відповіддю (0.7)
                timeout=12
            )

            result_text = response.choices[0].message.content.strip()
            logger.info(f"GPT SINGLE-PASS ВІДПОВІДЬ: {result_text}")

            parsed_result = json.loads(result_text)
            
            # Якщо це просто розмова
            if not parsed_result.get("isCommand", True):
                return {
                    "success": False, 
                    "casual_talk": True, 
                    "jarvis_response": parsed_result.get("jarvis_response", "Чим можу допомогти, сер?")
                }

            execution_plan = parsed_result.get("execution_plan", [])
            jarvis_response = parsed_result.get("jarvis_response", "Так, сер")
            
            # Збираємо список плагінів для контексту
            selected_plugins = [step.get("plugin") for step in execution_plan if step.get("plugin")]

            return {
                "success": True,
                "execution_plan": execution_plan,
                "jarvis_response": jarvis_response,
                "selected_plugins": selected_plugins
            }

        except Exception as e:
            import traceback
            error_msg = str(e)
            logger.error("Single-pass generation failed", extra={'error': error_msg, 'traceback': traceback.format_exc()})
            return {"success": False, "error": f"Помилка ШІ: {error_msg}"}
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



import time # Переконайся, що цей імпорт є на початку файлу smart_ai.py

async def process_smart_command(user_text):
    """Основна функція для обробки команд через ШІ (Однопрохідна система)"""
    global_start_time = time.time() # ⏱ СТАРТ ЗАГАЛЬНОГО ЧАСУ

    if not smart_assistant:
        logger.error("AI assistant not configured")
        return {"success": False, "message": "ШІ асистент не налаштовано."}

    try:
        from smart_plugin_manager import SmartPluginManager

        if not hasattr(smart_assistant, 'plugin_manager') or smart_assistant.plugin_manager is None:
                smart_assistant.plugin_manager = SmartPluginManager()

        # ⏱ ЗАМІР ЧАСУ ШІ
        ai_start_time = time.time()
        ai_result = await smart_assistant.process_single_pass(user_text)
        ai_duration = time.time() - ai_start_time
        print(f"\n[⏱ ТАЙМЕР] Запит до ШІ зайняв: {ai_duration:.2f} сек")

        await command_logger.log_command(user_text, "Single-pass execution", str(ai_result))

        if not ai_result.get("success"):
            if ai_result.get("casual_talk"):
                return {
                    "success": False, "message": "Розмова", "casual_talk": True,
                    "quick_response": ai_result.get("jarvis_response")
                }
            return {"success": False, "message": ai_result.get("error", "Невідома помилка")}

        execution_plan = ai_result.get("execution_plan", [])
        quick_response = ai_result.get("jarvis_response", "Виконую, сер")
        selected_plugins = ai_result.get("selected_plugins", [])

        try:
            import config_manager as cfg
            config = cfg.load_config()
        except Exception:
            config = {}

        if not execution_plan:
            return {"success": False, "message": "Пустий план виконання"}

        # 🔥 МАГІЯ ТУТ: Запускаємо озвучку ОДРАЗУ, не чекаючи плагінів
        print(f"[🔊 Jarvis каже]: {quick_response}")
        tts_task = None
        try:
            tts_task = asyncio.create_task(asyncio.to_thread(speak_text, quick_response, config))
        except Exception as e:
            print(f"Помилка запуску TTS: {e}")

        # ⏱ ЗАМІР ЧАСУ ВИКОНАННЯ ПЛАГІНІВ
        # ⏱ ЗАМІР ЧАСУ ВИКОНАННЯ ПЛАГІНІВ
        plugin_start_time = time.time()
        execution_results = []
        
        for plugin_info in execution_plan:
            plugin_name = plugin_info.get("plugin")
            for command_info in plugin_info.get("commands", []):
                command_name = command_info.get("command")
                params = command_info.get("params", {})

                import re
                clean_command_name = re.sub(r'_?\d+$', '', command_name)

                result = await smart_assistant.plugin_manager.execute_plugin_command(
                    plugin_name, clean_command_name, **params
                )
                execution_results.append({"plugin": plugin_name, "command": clean_command_name, "result": result})

                # 🔥 ДОДАЙ ЦЕ: Секундна пауза між командами, щоб Windows встиг опрацювати запуск
                await asyncio.sleep(1.0)

        plugin_duration = time.time() - plugin_start_time
        print(f"[⏱ ТАЙМЕР] Виконання плагінів зайняло: {plugin_duration:.2f} сек")

        successful_commands = [r for r in execution_results if r["result"].get("success")]

        if successful_commands:
            smart_assistant.update_conversation_context(user_text, quick_response, selected_plugins)
            
            for result in successful_commands:
                if "speak_text" in result.get("result", {}):
                    if tts_task: await tts_task 
                    speak_text(result["result"]["speak_text"], config)
                    break
        else:
            if tts_task: await tts_task
            speak_text("Вибачте, команду не вдалося виконати, сер", config)

        # 🔥 ДОДАЙ ЦЕ: Обов'язково чекаємо завершення базової фрази перед тим, як увімкнути мікрофон
        if tts_task and not tts_task.done():
            await tts_task

        total_duration = time.time() - global_start_time
        print(f"[⏱ ТАЙМЕР] Всього від отримання тексту до завершення: {total_duration:.2f} сек\n")

        return {
            "success": True,
            "action": {"type": "plugin_execution", "successful_count": len(successful_commands)},
            "message": "Команда виконана", "quick_response": quick_response
        }
    
    except Exception as e:
        import traceback
        logger.error("Smart command processing failed", extra={'error': str(e), 'traceback': traceback.format_exc()})
        return {"success": False, "message": f"Помилка: {str(e)}"}