import asyncio
import time
from datetime import datetime
from google import genai
from google.genai import types
from logger_config import get_logger
from audio_player import speak_text
from command_logger import command_logger
import speed_logger

logger = get_logger('smart_ai')

# Модель для основного роутингу команд
ROUTING_MODEL = "gemini-3.1-flash-lite-preview"
# Модель для запитів з плагінів (ask_gpt)
PLUGIN_MODEL = "gemini-3.1-flash-lite-preview"


class SmartAssistant:
    def __init__(self, api_key: str, model: str = ROUTING_MODEL):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.plugin_model = PLUGIN_MODEL
        self.plugin_manager = None
        self.conversation_history = []
        self.last_responses = []
        self.last_active_plugins = []
        # Gemini tools — будуються один раз після ініціалізації plugin_manager
        self._gemini_tools: list[types.Tool] | None = None

    async def _stream_gemini(
        self,
        contents,
        config: types.GenerateContentConfig,
        on_speak_ready=None,
    ):
        """Стримінг відповіді Gemini. Як тільки speak_response зібраний — викликає on_speak_ready(text).
        Повертає (parts_list, fc_count) де parts_list — список повних FunctionCall/text частин."""

        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def _stream_and_enqueue():
            """Читає стрім в окремому треді, кладе chunks в чергу. None = кінець."""
            try:
                for chunk in self.client.models.generate_content_stream(
                    model=self.model,
                    contents=contents,
                    config=config,
                ):
                    loop.call_soon_threadsafe(queue.put_nowait, chunk)
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, None)

        # Запускаємо стрімінг в окремому треді, не чекаємо завершення
        stream_future = loop.run_in_executor(None, _stream_and_enqueue)

        fc_accum = {}
        text_parts = []
        speak_ready_fired = False

        # Читаємо чергу в event loop — можемо реагувати на кожен чанк одразу
        while True:
            chunk = await queue.get()
            if chunk is None:
                break
            if not chunk.candidates:
                continue
            parts = chunk.candidates[0].content.parts or []
            for part in parts:
                if part.function_call:
                    fc = part.function_call
                    fc_accum[len(fc_accum)] = fc

                    # speak_response прийшов — одразу викликаємо callback (ми вже в event loop)
                    if fc.name == "speak_response" and not speak_ready_fired and on_speak_ready:
                        speak_ready_fired = True
                        args = dict(fc.args)
                        on_speak_ready(
                            args.get("text", "Так, сер"),
                            bool(args.get("is_command", True)),
                            args.get("transcript", ""),
                        )
                elif part.text and part.text.strip():
                    text_parts.append(part.text.strip())

        await stream_future  # переконуємось що тред завершився без помилок

        result_parts = [("fc", fc) for fc in fc_accum.values()]
        if text_parts:
            result_parts.append(("text", " ".join(text_parts)))

        fc_count = sum(1 for t, _ in result_parts if t == "fc")
        return result_parts, fc_count

    def build_gemini_tools(self) -> list[types.Tool]:
        """Конвертує плагіни в Gemini FunctionDeclaration. Викликається один раз при старті."""
        if not self.plugin_manager:
            return []

        declarations = []

        # speak_response — окремий tool для відповіді Jarvis
        declarations.append(types.FunctionDeclaration(
            name="speak_response",
            description=(
                "Визначає що саме скаже Jarvis у відповідь. "
                "ЗАВЖДИ викликай цю функцію разом з іншими командами. "
                "Відповідь має бути ультракороткою (1-5 слів). "
                "Для команд: 'Так, сер', 'Виконую', 'Секунду'. "
                "Для питань/рекомендацій: 'Зараз підберу', 'Обдумую варіанти'. "
                "Для розмови: природна коротка відповідь."
            ),
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "text": types.Schema(
                        type=types.Type.STRING,
                        description="Текст який скаже Jarvis"
                    ),
                    "is_command": types.Schema(
                        type=types.Type.BOOLEAN,
                        description="True якщо це виконання команди, False якщо розмова або питання"
                    ),
                    "transcript": types.Schema(
                        type=types.Type.STRING,
                        description="Точна фраза яку сказав користувач (дослівно, як почув)"
                    )
                },
                required=["text", "is_command"]
            )
        ))

        # Плагіни — кожна команда стає окремою FunctionDeclaration
        for plugin_name, plugin in self.plugin_manager.plugins.items():
            try:
                for cmd_name, cmd_desc in plugin.commands.items():
                    declarations.append(types.FunctionDeclaration(
                        name=f"{plugin_name}__{cmd_name}",
                        description=f"[{plugin_name}] {cmd_desc}",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "value": types.Schema(
                                    type=types.Type.STRING,
                                    description="Назва/текст (пісня, програма, виконавець тощо)"
                                ),
                                "level": types.Schema(
                                    type=types.Type.STRING,
                                    description="Числовий рівень: гучність/яскравість. Монітор: '1,25' або 'all,50'"
                                )
                            },
                            required=[]
                        )
                    ))
            except Exception as e:
                logger.error(f"Failed to build tool for plugin {plugin_name}", extra={"error": str(e)})

        self._gemini_tools = [types.Tool(function_declarations=declarations)]
        logger.info(f"Built {len(declarations)} Gemini tools from {len(self.plugin_manager.plugins)} plugins")
        return self._gemini_tools

    def update_conversation_context(self, user_text: str, jarvis_response: str, executed_plugins: list = None):
        """Оновлює контекст розмови."""
        self.conversation_history.append(user_text)
        if len(self.conversation_history) > 2:
            self.conversation_history.pop(0)

        self.last_responses.append(jarvis_response)
        if len(self.last_responses) > 2:
            self.last_responses.pop(0)

        if executed_plugins:
            self.last_active_plugins = executed_plugins
            logger.info(f"Context updated with plugins: {executed_plugins}")

    async def process_single_pass(self, user_text: str, on_speak_ready=None) -> dict:
        """Однопрохідний запит до Gemini з function calling (streaming)."""
        try:
            if self._gemini_tools is None:
                self.build_gemini_tools()

            context_block = ""
            if self.conversation_history and self.last_responses:
                conversations = []
                for i in range(min(len(self.conversation_history), len(self.last_responses), 2)):
                    idx = -(i + 1)
                    conversations.insert(0,
                        f"Користувач: {self.conversation_history[idx]}\n"
                        f"Jarvis: {self.last_responses[idx]}"
                    )
                if self.last_active_plugins:
                    conversations[-1] += f"\nВикористані плагіни: {self.last_active_plugins}"
                context_block = (
                    "\n\nКОНТЕКСТ ПОПЕРЕДНЬОЇ РОЗМОВИ:\n"
                    + "\n".join(conversations)
                    + "\n\nПРАВИЛА ДЛЯ КОНТЕКСТУ:\n"
                    "- Використовуй ті ж плагіни ТІЛЬКИ якщо нова репліка є чіткою командою або явним продовженням задачі.\n"
                    "- Якщо репліка — випадкова фраза, прощання, реакція ('прикольно', 'окей'), незрозумілий набір слів або фраза не до тебе — НЕ викликай жодних плагінів, лише speak_response з is_command=false.\n"
                    "- Ознаки НЕ-команди: 'пока', 'дякую', 'добре', 'ок', 'прикольно', 'все', безглузді слова, суміш мов без сенсу."
                )

            system_instruction = (
                "Ти — JARVIS, розумний голосовий асистент. "
                "Аналізуй репліку та викликай потрібні функції.\n\n"
                "ПРАВИЛА:\n"
                "1. ЗАВЖДИ викликай speak_response — це голос Jarvis.\n"
                "2. Якщо репліка містить 'напиши'/'надрукуй'/'введи' — це keyboard_typing.\n"
                "3. Якщо це чиста розмова (привіт, як справи, пока, дякую) — тільки speak_response з is_command=false.\n"
                "4. Можна викликати кілька функцій одночасно.\n"
                "5. Відповідь speak_response — ультракоротка, 1-5 слів.\n"
                "6. ЗАБОРОНЕНО викликати плагіни на нечіткі, беззмістовні або не адресовані тобі фрази."
                + context_block
            )

            user_prompt = f'Користувач каже: "{user_text}"'

            logger.info(f"Sending to Gemini (stream): {user_text}")
            _timer = speed_logger.get_session()
            if _timer: _timer.on_gemini_start()

            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=self._gemini_tools,
                temperature=0.4,
                max_output_tokens=400,
            )

            result_parts, fc_count = await self._stream_gemini(
                contents=user_prompt,
                config=config,
                on_speak_ready=on_speak_ready,
            )

            if _timer:
                _timer.on_gemini_done(fc_count)

            command_logger.log_ai_exchange(system_instruction, user_prompt, result_parts, tools=self._gemini_tools)

            # Розбираємо зібрані parts
            jarvis_response = "Так, сер"
            is_command = True
            execution_plan = []

            if not result_parts:
                return {"success": False, "casual_talk": True, "is_command": False, "jarvis_response": ""}

            for kind, data in result_parts:
                if kind == "fc":
                    fc = data
                    logger.info(f"Function call: {fc.name} args={dict(fc.args)}")
                    if fc.name == "speak_response":
                        args_dict = dict(fc.args)
                        jarvis_response = args_dict.get("text", "Так, сер")
                        is_command = bool(args_dict.get("is_command", True))
                    elif "__" in fc.name:
                        plugin_name, cmd_name = fc.name.split("__", 1)
                        args_dict = dict(fc.args)
                        params = {}
                        value = args_dict.get("value", "")
                        level = args_dict.get("level", "")
                        if value:
                            params["value"] = value
                        if level:
                            params["level"] = level
                        execution_plan.append({"plugin": plugin_name, "command": cmd_name, "params": params})
                elif kind == "text":
                    logger.info(f"Text response fallback: {data}")
                    jarvis_response = data

            if execution_plan and self.plugin_manager:
                valid_plan = []
                for step in execution_plan:
                    plugin = self.plugin_manager.plugins.get(step["plugin"])
                    if plugin and step["command"] in plugin.commands:
                        valid_plan.append(step)
                    else:
                        logger.warning(f"Gemini вигадав неіснуючу команду: {step['plugin']}.{step['command']} — ігнорую")
                execution_plan = valid_plan

            if not execution_plan:
                return {"success": False, "casual_talk": True, "is_command": is_command, "jarvis_response": jarvis_response}

            return {
                "success": True,
                "execution_plan": execution_plan,
                "jarvis_response": jarvis_response,
                "selected_plugins": list({step["plugin"] for step in execution_plan}),
            }

        except Exception as e:
            import traceback
            logger.error(f"Single-pass generation failed: {type(e).__name__}: {e}\n{traceback.format_exc()}")
            return {"success": False, "error": f"Помилка ШІ: {str(e)}"}

    async def process_audio_pass(self, audio_bytes: bytes, on_speak_ready=None) -> dict:
        """Однопрохідний запит до Gemini з нативним аудіо + function calling (streaming)."""
        try:
            if self._gemini_tools is None:
                self.build_gemini_tools()

            context_block = ""
            if self.conversation_history and self.last_responses:
                conversations = []
                for i in range(min(len(self.conversation_history), len(self.last_responses), 2)):
                    idx = -(i + 1)
                    conversations.insert(0,
                        f"Користувач: {self.conversation_history[idx]}\n"
                        f"Jarvis: {self.last_responses[idx]}"
                    )
                if self.last_active_plugins:
                    conversations[-1] += f"\nВикористані плагіни: {self.last_active_plugins}"
                context_block = (
                    "\n\nКОНТЕКСТ ПОПЕРЕДНЬОЇ РОЗМОВИ:\n"
                    + "\n".join(conversations)
                    + "\n\nПРАВИЛА ДЛЯ КОНТЕКСТУ:\n"
                    "- Використовуй ті ж плагіни ТІЛЬКИ якщо нова репліка є чіткою командою або явним продовженням задачі.\n"
                    "- Якщо репліка — випадкова фраза, прощання, реакція ('прикольно', 'окей'), незрозумілий набір слів або фраза не до тебе — НЕ викликай жодних плагінів, лише speak_response з is_command=false.\n"
                    "- Ознаки НЕ-команди: 'пока', 'дякую', 'добре', 'ок', 'прикольно', 'все', безглузді слова, суміш мов без сенсу."
                )

            system_instruction = (
                "Ти — JARVIS, розумний голосовий асистент. "
                "Користувач говорить голосом — розпізнай що він сказав і викликай потрібні функції.\n\n"
                "ПРАВИЛА:\n"
                "1. ЗАВЖДИ викликай speak_response — це голос Jarvis. У полі 'transcript' передай ДОСЛІВНО що сказав користувач.\n"
                "2. Якщо репліка містить 'напиши'/'надрукуй'/'введи' — це keyboard_typing.\n"
                "3. Якщо це чиста розмова (привіт, як справи, пока, дякую) — тільки speak_response з is_command=false.\n"
                "4. Можна викликати кілька функцій одночасно.\n"
                "5. Відповідь speak_response — ультракоротка, 1-5 слів.\n"
                "6. ЗАБОРОНЕНО викликати плагіни на нечіткі, беззмістовні або не адресовані тобі фрази."
                + context_block
            )

            logger.info("Sending audio to Gemini (native audio streaming)")
            _timer = speed_logger.get_session()
            if _timer: _timer.on_gemini_start()

            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                tools=self._gemini_tools,
                temperature=0.4,
                max_output_tokens=400,
            )

            result_parts, fc_count = await self._stream_gemini(
                contents=[types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")],
                config=config,
                on_speak_ready=on_speak_ready,
            )

            if _timer:
                _timer.on_gemini_done(fc_count)

            command_logger.log_ai_exchange(system_instruction, "[AUDIO INPUT]", result_parts, tools=self._gemini_tools)

            jarvis_response = "Так, сер"
            is_command = True
            transcript = ""
            execution_plan = []

            if not result_parts:
                return {"success": False, "casual_talk": True, "is_command": False, "jarvis_response": ""}

            for kind, data in result_parts:
                if kind == "fc":
                    fc = data
                    logger.info(f"Function call: {fc.name} args={dict(fc.args)}")
                    if fc.name == "speak_response":
                        args_dict = dict(fc.args)
                        jarvis_response = args_dict.get("text", "Так, сер")
                        is_command = bool(args_dict.get("is_command", True))
                        transcript = args_dict.get("transcript", "")
                        if transcript:
                            logger.info(f"Gemini transcript: {transcript}")
                    elif "__" in fc.name:
                        plugin_name, cmd_name = fc.name.split("__", 1)
                        args_dict = dict(fc.args)
                        params = {}
                        value = args_dict.get("value", "")
                        level = args_dict.get("level", "")
                        if value:
                            params["value"] = value
                        if level:
                            params["level"] = level
                        execution_plan.append({"plugin": plugin_name, "command": cmd_name, "params": params})
                elif kind == "text":
                    jarvis_response = data

            if execution_plan and self.plugin_manager:
                valid_plan = []
                for step in execution_plan:
                    plugin = self.plugin_manager.plugins.get(step["plugin"])
                    if plugin and step["command"] in plugin.commands:
                        valid_plan.append(step)
                    else:
                        logger.warning(f"Gemini вигадав неіснуючу команду: {step['plugin']}.{step['command']} — ігнорую")
                execution_plan = valid_plan

            if not execution_plan:
                return {"success": False, "casual_talk": True, "is_command": is_command, "jarvis_response": jarvis_response, "transcript": transcript}

            return {
                "success": True,
                "transcript": transcript,
                "execution_plan": execution_plan,
                "jarvis_response": jarvis_response,
                "selected_plugins": list({step["plugin"] for step in execution_plan}),
            }

        except Exception as e:
            import traceback
            logger.error(f"Audio-pass generation failed: {type(e).__name__}: {e}\n{traceback.format_exc()}")
            return {"success": False, "error": f"Помилка ШІ (audio): {str(e)}"}


# Глобальний екземпляр
smart_assistant: SmartAssistant | None = None


def initialize_smart_assistant(api_key: str, routing_model: str = None, plugin_model: str = None) -> bool:
    """Ініціалізує ШІ асистента з Gemini API ключем."""
    global smart_assistant
    if api_key and api_key != "YOUR_OPENAI_API_KEY_HERE":
        try:
            model = routing_model or ROUTING_MODEL
            smart_assistant = SmartAssistant(api_key, model=model)
            if plugin_model:
                smart_assistant.plugin_model = plugin_model
            logger.info(f"Smart AI assistant initialized: routing={model}, plugin={smart_assistant.plugin_model}")
            return True
        except Exception as e:
            logger.error("Failed to initialize Smart AI assistant", extra={"error": str(e)})
            smart_assistant = None
            return False
    else:
        logger.info("Gemini API key not provided — AI assistant disabled")
        return False


async def process_smart_command(user_text: str) -> dict:
    """Основна функція для обробки команд через ШІ."""
    global_start_time = time.time()

    if not smart_assistant:
        logger.error("AI assistant not configured")
        return {"success": False, "message": "ШІ асистент не налаштовано."}

    try:
        from smart_plugin_manager import SmartPluginManager

        if smart_assistant.plugin_manager is None:
            smart_assistant.plugin_manager = SmartPluginManager()
            smart_assistant.build_gemini_tools()

        try:
            import config_manager as cfg
            config = cfg.load_config()
        except Exception:
            config = {}

        # TTS запускається одразу як speak_response приходить зі стріму — ще до кінця Gemini
        _timer = speed_logger.get_session()
        tts_task = None
        quick_response_holder = ["Виконую, сер"]

        def on_speak_ready(text, is_cmd, transcript):
            nonlocal tts_task
            quick_response_holder[0] = text
            print(f"[🔊 Jarvis каже]: {text}")
            if _timer: _timer.on_tts_start(text)
            try:
                tts_task = asyncio.get_running_loop().create_task(
                    asyncio.to_thread(speak_text, text, config)
                )
            except Exception as e:
                print(f"Помилка запуску TTS: {e}")

        ai_start_time = time.time()
        ai_result = await smart_assistant.process_single_pass(user_text, on_speak_ready=on_speak_ready)
        ai_duration = time.time() - ai_start_time
        print(f"\n[⏱ ТАЙМЕР] Запит до ШІ зайняв: {ai_duration:.2f} сек")

        await command_logger.log_command(user_text, ai_result)

        quick_response = ai_result.get("jarvis_response", quick_response_holder[0])
        selected_plugins = ai_result.get("selected_plugins", [])

        if not ai_result.get("success"):
            # Якщо casual_talk і TTS ще не запустився — запускаємо зараз
            if ai_result.get("casual_talk"):
                if tts_task is None and quick_response:
                    if _timer: _timer.on_tts_start(quick_response)
                    tts_task = asyncio.create_task(asyncio.to_thread(speak_text, quick_response, config))
                if tts_task:
                    await tts_task
                    if _timer: _timer.on_tts_done()
                return {
                    "success": False,
                    "message": "Розмова",
                    "casual_talk": True,
                    "is_command": ai_result.get("is_command", True),
                    "quick_response": quick_response,
                }
            return {"success": False, "message": ai_result.get("error", "Невідома помилка")}

        execution_plan = ai_result.get("execution_plan", [])
        if not execution_plan:
            return {"success": False, "message": "Пустий план виконання"}

        # Виконуємо плагіни паралельно з TTS що вже йде
        execution_results = []
        for step in execution_plan:
            plugin_name = step["plugin"]
            command_name = step["command"]
            params = step.get("params", {})
            if _timer: _timer.on_plugin_start(plugin_name, command_name)
            result = await smart_assistant.plugin_manager.execute_plugin_command(
                plugin_name, command_name, **params
            )
            if _timer: _timer.on_plugin_done(plugin_name, command_name, result.get("success", False))
            execution_results.append({"plugin": plugin_name, "command": command_name, "result": result})

        successful_commands = [r for r in execution_results if r["result"].get("success")]

        # Чекаємо завершення швидкої відповіді
        if tts_task:
            await tts_task
        if _timer: _timer.on_tts_done()

        if successful_commands:
            smart_assistant.update_conversation_context(user_text, quick_response, selected_plugins)
            for result in successful_commands:
                follow_up = (
                    result.get("result", {}).get("speak_text")
                    or result.get("result", {}).get("message")
                )
                if follow_up:
                    if _timer: _timer.on_tts_start(follow_up)
                    await asyncio.to_thread(speak_text, follow_up, config)
                    if _timer: _timer.on_tts_done()
                    break
        else:
            await asyncio.to_thread(speak_text, "Вибачте, команду не вдалося виконати, сер", config)

        total_duration = time.time() - global_start_time
        print(f"[⏱ ТАЙМЕР] Всього: {total_duration:.2f} сек\n")

        return {
            "success": True,
            "action": {"type": "plugin_execution", "successful_count": len(successful_commands)},
            "message": "Команда виконана",
            "quick_response": quick_response,
        }

    except Exception as e:
        import traceback
        logger.error("Smart command processing failed", extra={
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        return {"success": False, "message": f"Помилка: {str(e)}"}


async def process_smart_command_audio(audio_bytes: bytes) -> dict:
    """Обробка команди через нативне аудіо Gemini (замість Google STT)."""
    global_start_time = time.time()

    if not smart_assistant:
        return {"success": False, "message": "ШІ асистент не налаштовано."}

    try:
        from smart_plugin_manager import SmartPluginManager

        if smart_assistant.plugin_manager is None:
            smart_assistant.plugin_manager = SmartPluginManager()
            smart_assistant.build_gemini_tools()

        try:
            import config_manager as cfg
            config = cfg.load_config()
        except Exception:
            config = {}

        # TTS запускається одразу як speak_response приходить зі стріму — ще до кінця Gemini
        _timer = speed_logger.get_session()
        tts_task = None
        quick_response_holder = ["Виконую, сер"]

        def on_speak_ready(text, is_cmd, transcript):
            nonlocal tts_task
            quick_response_holder[0] = text
            print(f"[🔊 Jarvis каже]: {text}")
            if _timer: _timer.on_tts_start(text)
            try:
                tts_task = asyncio.get_running_loop().create_task(
                    asyncio.to_thread(speak_text, text, config)
                )
            except Exception as e:
                print(f"Помилка запуску TTS: {e}")

        ai_start_time = time.time()
        ai_result = await smart_assistant.process_audio_pass(audio_bytes, on_speak_ready=on_speak_ready)
        ai_duration = time.time() - ai_start_time
        print(f"\n[⏱ ТАЙМЕР] Запит до Gemini Audio зайняв: {ai_duration:.2f} сек")

        transcript = ai_result.get("transcript", "")
        user_label = f"[AUDIO] {transcript}" if transcript else "[AUDIO]"
        await command_logger.log_command(user_label, ai_result)

        quick_response = ai_result.get("jarvis_response", quick_response_holder[0])
        selected_plugins = ai_result.get("selected_plugins", [])

        if not ai_result.get("success"):
            if ai_result.get("casual_talk"):
                if tts_task is None and quick_response:
                    if _timer: _timer.on_tts_start(quick_response)
                    tts_task = asyncio.create_task(asyncio.to_thread(speak_text, quick_response, config))
                if tts_task:
                    await tts_task
                    if _timer: _timer.on_tts_done()
                return {
                    "success": False,
                    "message": "Розмова",
                    "casual_talk": True,
                    "is_command": ai_result.get("is_command", True),
                    "quick_response": quick_response,
                }
            return {"success": False, "message": ai_result.get("error", "Невідома помилка")}

        execution_plan = ai_result.get("execution_plan", [])
        if not execution_plan:
            return {"success": False, "message": "Пустий план виконання"}

        # Виконуємо плагіни паралельно з TTS що вже йде
        execution_results = []
        for step in execution_plan:
            plugin_name = step["plugin"]
            command_name = step["command"]
            params = step.get("params", {})
            if _timer: _timer.on_plugin_start(plugin_name, command_name)
            result = await smart_assistant.plugin_manager.execute_plugin_command(
                plugin_name, command_name, **params
            )
            if _timer: _timer.on_plugin_done(plugin_name, command_name, result.get("success", False))
            execution_results.append({"plugin": plugin_name, "command": command_name, "result": result})

        successful_commands = [r for r in execution_results if r["result"].get("success")]

        # Чекаємо завершення швидкої відповіді
        if tts_task:
            await tts_task
        if _timer: _timer.on_tts_done()

        if successful_commands:
            smart_assistant.update_conversation_context(transcript or "[audio]", quick_response, selected_plugins)
            for result in successful_commands:
                follow_up = (
                    result.get("result", {}).get("speak_text")
                    or result.get("result", {}).get("message")
                )
                if follow_up:
                    if _timer: _timer.on_tts_start(follow_up)
                    await asyncio.to_thread(speak_text, follow_up, config)
                    if _timer: _timer.on_tts_done()
                    break
        else:
            if _timer: _timer.on_tts_start("Вибачте, команду не вдалося виконати, сер")
            await asyncio.to_thread(speak_text, "Вибачте, команду не вдалося виконати, сер", config)
            if _timer: _timer.on_tts_done()

        total_duration = time.time() - global_start_time
        print(f"[⏱ ТАЙМЕР] Всього (audio): {total_duration:.2f} сек\n")

        return {
            "success": True,
            "action": {"type": "plugin_execution", "successful_count": len(successful_commands)},
            "message": "Команда виконана",
            "quick_response": quick_response,
            "is_command": True,
        }

    except Exception as e:
        import traceback
        logger.error("Audio command processing failed", extra={
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        return {"success": False, "message": f"Помилка: {str(e)}"}