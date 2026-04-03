# wake_word.py
import datetime
import time
import asyncio
from transcriber import OnlineTranscriber
from command_manager import CommandManager
import settings
from audio_player import play_listen_sound, play_end_sound, handle_wake_word_response, handle_session_end
import config_manager as cfg
from media_controller import media_manager
import speed_logger

class WakeWordHandler:
    def __init__(self, tray_manager):
        self.tray_manager = tray_manager
        self.last_detection_time = 0
        self.detection_cooldown = 1.0
        self.transcriber = OnlineTranscriber()
        self.command_manager = CommandManager()
        config = cfg.load_config()
        self.use_gemini_stt = config.get("useGeminiSTT", False)

    def on_wake_word_detected(self, wake_word):
        current_time = time.time()
        if current_time - self.last_detection_time < self.detection_cooldown:
            return
        self.last_detection_time = current_time

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"\n🔥 [{timestamp}] WAKE WORD ({wake_word})!")

        mode = "gemini_audio" if self.use_gemini_stt else "google_stt"
        speed_logger.start_session(mode)

        # 1. Розумна пауза: ставить на паузу, ТІЛЬКИ ЯКЩО щось грає
        media_manager.pause_if_playing()

        self.tray_manager.set_icon_state(True)

        # Завантажуємо конфігурацію для правильного вибору звук/TTS
        config = cfg.load_config()
        handle_wake_word_response(config)

        self.listen_for_commands()

        handle_session_end(config)
        self.tray_manager.set_icon_state(False)

        # 2. Розумне відновлення: відновлює, ТІЛЬКИ ЯКЩО ми самі ставили на паузу
        time.sleep(0.5)
        media_manager.resume_if_paused()

        speed_logger.end_session()
        print("Сесію команд завершено. Повертаюсь до очікування wake word.")

    def listen_for_commands(self):
        """Синхронна версія для зворотної сумісності."""
        # Запускаємо async версію в новому event loop
        if asyncio._get_running_loop() is None:
            asyncio.run(self.listen_for_commands_async())
        else:
            # Якщо вже є event loop, використовуємо task
            task = asyncio.create_task(self.listen_for_commands_async())
            # Блокуємо до завершення
            asyncio.get_event_loop().run_until_complete(task)

    async def listen_for_commands_async(self):
        """Async версія слухання команд з покращеною логікою."""
        session_start_time = time.time()
        session_end_time = session_start_time + settings.COMMAND_SESSION_TIMEOUT

        print("Початок сесії слухання команд...")

        while time.time() < session_end_time and self.tray_manager.is_running:
            remaining_time = session_end_time - time.time()
            if remaining_time <= 0:
                break

            # Додаємо silence timeout з config
            silence_timeout = getattr(settings, 'SILENCE_TIMEOUT', 5.0)

            try:
                transcribe_start = time.time()
                import smart_ai

                if self.use_gemini_stt and smart_ai.smart_assistant:
                    # Gemini Native Audio — записуємо аудіо і шлемо байти напряму
                    audio_bytes = await asyncio.to_thread(
                        self.transcriber.listen_and_get_audio, remaining_time
                    )
                    transcribe_duration = time.time() - transcribe_start
                    print(f"[⏱ ТАЙМЕР] Запис аудіо зайняв: {transcribe_duration:.2f} сек")

                    if not audio_bytes:
                        print("[DEBUG] Таймаут слухання або тиша. Завершення сесії.")
                        break

                    size_kb = len(audio_bytes) / 1024
                    size_mb = size_kb / 1024
                    print(f"[🎤 Gemini Audio] Відправляю {size_kb:.1f} KB ({size_mb:.2f} MB)...")

                    result = await smart_ai.process_smart_command_audio(audio_bytes)

                    if result.get("success"):
                        new_end_time = time.time() + settings.CONTINUOUS_LISTEN_SECONDS
                        session_end_time = max(session_end_time, new_end_time)
                        print(f"[DEBUG] Сесію продовжено. Залишилось ~{session_end_time - time.time():.1f}с")
                    elif result.get("casual_talk") and not result.get("is_command", True):
                        print("[DEBUG] Gemini Audio: не команда — завершуємо сесію.")
                        break
                    continue
                else:
                    # Стандартний режим: Google STT → текст → Gemini
                    transcript = await self.transcriber.listen_with_silence_detection(
                        max_timeout=remaining_time,
                        silence_timeout=silence_timeout
                    )
                    transcribe_duration = time.time() - transcribe_start
                    print(f"[⏱ ТАЙМЕР] Слухання та розпізнавання тексту зайняло: {transcribe_duration:.2f} сек")

                    if not transcript:
                        print("[DEBUG] Таймаут слухання або тиша. Завершення сесії.")
                        break

                    transcript_text = transcript.strip()
                    print(f"🔥 Ви сказали: {transcript_text}")
                    command, argument = await self.command_manager.find_command(transcript_text)

                if command and command.get('type') == 'smart_ai':
                    result = await self.command_manager.execute_command(command, argument)
                    if result and isinstance(result, dict):
                        print(result.get('response_text', 'Команду виконано'))
                    # Продовжуємо сесію після успішної команди
                    new_end_time = time.time() + settings.CONTINUOUS_LISTEN_SECONDS
                    session_end_time = max(session_end_time, new_end_time)
                    print(f"[DEBUG] Сесію продовжено. Залишилось ~{session_end_time - time.time():.1f}с")
                elif command and command.get('type') == 'casual':
                    # Gemini сказав що це не команда (is_command=False) — завершуємо сесію
                    if not command.get('is_command', True):
                        print("[DEBUG] Gemini: не команда — завершуємо сесію.")
                        break
                    print("Розмова без команди, слухаю далі...")
                else:
                    print("Команду не знайдено, слухаю далі...")

            except asyncio.CancelledError:
                print("[DEBUG] Слухання команд скасовано")
                break
            except Exception as e:
                print(f"[DEBUG] Помилка під час слухання: {e}")
                break