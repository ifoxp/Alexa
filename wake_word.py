# wake_word.py
import datetime
import time
from stt.online_transcriber import OnlineTranscriber 
from command_manager import CommandManager
from audio_player import play_listen_sound, play_end_sound
import config_manager as cfg # Щоб отримати мову
import settings # Для таймаутів

class WakeWordHandler:
    def __init__(self, tray_manager):
        self.tray_manager = tray_manager # Зберігаємо посилання на трей
        self.last_detection_time = 0
        self.detection_cooldown = 1.0 # Можна винести в settings/config
        self.transcriber = OnlineTranscriber()
        self.command_manager = CommandManager()
        # Встановлюємо мову з конфігу один раз при старті
        config = cfg.load_config() 
        self.transcriber.set_language(config.get("language", "uk-UA"))

    def on_wake_word_detected(self, wake_word):
        current_time = time.time()
        if current_time - self.last_detection_time < self.detection_cooldown:
            return
        self.last_detection_time = current_time

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"\n🔥 [{timestamp}] WAKE WORD ({wake_word})!")
        
        self.tray_manager.set_icon_state(True) # Зелена іконка
        play_listen_sound()
        
        self.listen_for_commands()
        
        play_end_sound()
        self.tray_manager.set_icon_state(False) # Біла іконка
        print("Сесію команд завершено.")

    def listen_for_commands(self):
        """Основний цикл слухання команд."""
        session_end_time = time.time() + settings.COMMAND_SESSION_TIMEOUT
        last_activity_time = time.time() 

        print("🎧 Початок сесії слухання команд...")
        while time.time() < session_end_time and self.tray_manager.is_running:
            time_since_last_activity = time.time() - last_activity_time
            if time_since_last_activity > settings.CONTINUOUS_LISTEN_SECONDS:
                print(f"[DEBUG] {settings.CONTINUOUS_LISTEN_SECONDS} секунд тиші. Завершення сесії.")
                break

            remaining_time_total = session_end_time - time.time()
            remaining_time_wait = settings.CONTINUOUS_LISTEN_SECONDS - time_since_last_activity
            listen_timeout = max(0.1, min(remaining_time_total, remaining_time_wait)) # Беремо менший таймаут

            transcript = self.transcriber.listen_and_transcribe(timeout=listen_timeout)

            if transcript:
                last_activity_time = time.time() 
                transcript_text = transcript.strip()
                print(f"💬 Ви сказали: {transcript_text}")

                command, argument = self.command_manager.find_command(transcript_text)
        
                if command:
                    self.command_manager.execute_command(command, argument)
                    # Якщо команда вимагає аргумент, ймовірно, завершуємо сесію
                    # або якщо це проста команда, також можна завершити
                    # (можна додати поле в JSON 'end_session_after_exec': true/false)
                    break 
                else:
                    print(f"🤷 Команду не знайдено, слухаю далі...")
            else:
                 # Якщо listen_and_transcribe повернув None (таймаут або помилка),
                 # цикл while перевірить загальний таймаут і таймаут тиші
                 pass