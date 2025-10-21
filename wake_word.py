# wake_word.py
import datetime
import time
from stt.online_transcriber import OnlineTranscriber 
from command_manager import CommandManager
import settings
from audio_player import play_listen_sound, play_end_sound
from media_controller import media_manager # <-- ІМПОРТУЄМО НОВИЙ МЕНЕДЖЕР

class WakeWordHandler:
    def __init__(self, tray_manager):
        self.tray_manager = tray_manager
        self.last_detection_time = 0
        self.detection_cooldown = 1.0
        self.transcriber = OnlineTranscriber()
        self.command_manager = CommandManager()

    def on_wake_word_detected(self, wake_word):
        current_time = time.time()
        if current_time - self.last_detection_time < self.detection_cooldown:
            return
        self.last_detection_time = current_time

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"\n🔥 [{timestamp}] WAKE WORD ({wake_word})!")
        
        # 1. Розумна пауза: ставить на паузу, ТІЛЬКИ ЯКЩО щось грає
        media_manager.pause_if_playing()
        
        self.tray_manager.set_icon_state(True)
        play_listen_sound()
        
        self.listen_for_commands()
        
        play_end_sound()
        self.tray_manager.set_icon_state(False)
        
        # 2. Розумне відновлення: відновлює, ТІЛЬКИ ЯКЩО ми самі ставили на паузу
        time.sleep(0.5) 
        media_manager.resume_if_paused()
        
        print("Сесію команд завершено. Повертаюсь до очікування wake word.")

    def listen_for_commands(self):
        # ... (код цього методу залишається без змін) ...
        session_end_time = time.time() + settings.COMMAND_SESSION_TIMEOUT
        
        print("🎧 Початок сесії слухання команд...")
        while time.time() < session_end_time and self.tray_manager.is_running:
            remaining_time = session_end_time - time.time()
            if remaining_time <= 0:
                break
            
            transcript = self.transcriber.listen_and_transcribe(timeout=remaining_time)

            if transcript:
                transcript_text = transcript.strip()
                print(f"💬 Ви сказали: {transcript_text}")

                command, argument = self.command_manager.find_command(transcript_text)
        
                if command:
                    self.command_manager.execute_command(command, argument)
                    new_end_time = time.time() + settings.CONTINUOUS_LISTEN_SECONDS
                    session_end_time = max(session_end_time, new_end_time)
                    print(f"[DEBUG] Сесію продовжено. Залишилось ~{session_end_time - time.time():.1f}с")
                else:
                    print(f"🤷 Команду не знайдено, слухаю далі...")
            else:
                print("[DEBUG] Таймаут слухання. Завершення сесії.")
                break