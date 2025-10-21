import datetime
import time
from stt.online_transcriber import OnlineTranscriber 
from command_manager import CommandManager
import settings
from audio_player import play_listen_sound, play_end_sound # <-- НОВИЙ ІМПОРТ

class WakeWordHandler:
    def __init__(self):
        self.last_detection_time = 0
        self.detection_cooldown = settings.DETECTION_COOLDOWN
        self.transcriber = OnlineTranscriber()
        self.command_manager = CommandManager()

    def on_wake_word_detected(self, wake_word):
        current_time = time.time()
        if current_time - self.last_detection_time < self.detection_cooldown:
            return
        self.last_detection_time = current_time

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"\n🔥 [{timestamp}] WAKE WORD ({wake_word})!")
        
        # Відтворюємо звук початку слухання
        play_listen_sound()
        
        # Починаємо сесію слухання команд
        self.listen_for_commands()
        
        # Відтворюємо звук кінця сесії
        play_end_sound()
        print("Сесію команд завершено. Повертаюсь до очікування wake word.")

    def listen_for_commands(self):
        """Основний цикл слухання команд."""
        session_end_time = time.time() + settings.COMMAND_SESSION_TIMEOUT
        last_activity_time = time.time() # Час останньої розпізнаної фрази (команди чи ні)

        while time.time() < session_end_time:
            # Перевіряємо, чи не минуло 5 секунд тиші після останньої активності
            if time.time() - last_activity_time > settings.CONTINUOUS_LISTEN_SECONDS:
                print("[DEBUG] 5 секунд тиші. Завершення сесії.")
                break

            # Вираховуємо, скільки часу залишилось
            remaining_time = session_end_time - time.time()
            
            # Слухаємо наступну фразу
            transcript = self.transcriber.listen_and_transcribe(timeout=remaining_time)

            if transcript:
                last_activity_time = time.time() # Оновлюємо час активності
                transcript_text = transcript.strip()
                print(f" M Ви сказали: {transcript_text}")

                command, argument = self.command_manager.find_command(transcript_text)
        
                if command:
                    self.command_manager.execute_command(command, argument)
                    # Якщо команда вимагає аргумент, ми, ймовірно, хочемо завершити сесію
                    if command.get("requires_argument"):
                         break
                else:
                    print(f" M Команду не знайдено, слухаю далі...")
            
        # Цикл завершився (або через таймаут, або через 5с тиші)