# main.py
import time
import struct
import pyaudio
import pvporcupine
import threading
from wake_word import WakeWordHandler
from tray_manager import TrayManager
import config_manager as cfg
import settings # Для аудіо параметрів

# --- Глобальні змінні ---
porcupine = None
stream = None
audio = None
config = {} # Словник для завантаженої конфігурації

def main_loop(tray_manager):
    """Основний цикл, що слухає wake word."""
    global stream, porcupine, config
    
    # Використовуємо AccessKey та інші параметри з config
    try:
        porcupine = pvporcupine.create(
            access_key=config["picovoiceAccessKey"],
            keywords=[config["wakeWordStandard"]], # Використовуємо одне слово з конфігу
            sensitivities=[config["sensitivity"]]
        )
        print(f"✅ Модель Porcupine '{config['wakeWordStandard']}' завантажена")

        handler = WakeWordHandler(tray_manager) # Передаємо tray_manager
        
        # Використовуємо налаштування мови з конфігу
        handler.transcriber.set_language(config["language"])
        
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=settings.FORMAT,
            channels=settings.CHANNELS,
            rate=porcupine.sample_rate,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )
        print(f"🎤 Слухаю '{config['wakeWordStandard']}'...")

        while tray_manager.is_running:
            try:
                pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
                audio_data = struct.unpack_from("h" * porcupine.frame_length, pcm)
                keyword_index = porcupine.process(audio_data)

                if keyword_index >= 0: # Wake word виявлено
                    handler.on_wake_word_detected(config["wakeWordStandard"])

            except (IOError, struct.error, OSError) as e:
                # Ігноруємо помилки читання потоку, які можуть виникнути при закритті
                if tray_manager.is_running:
                     print(f"Помилка читання аудіо потоку: {e}")
                time.sleep(0.1) # Невелика пауза
                continue
            except Exception as e:
                 print(f"❌ Неочікувана помилка в основному циклі: {e}")
                 break # Виходимо з циклу при серйозних помилках

    except pvporcupine.PorcupineActivationLimitError:
         print("ПОМИЛКА: Досягнуто ліміт активацій Picovoice для цього AccessKey.")
         # Тут можна показати повідомлення користувачу через трей
    except Exception as e:
        print(f"❌ Критична помилка ініціалізації/роботи Porcupine: {e}")
    finally:
        print("Зупинка основного циклу...")
        if porcupine: porcupine.delete()
        if stream:
            stream.stop_stream()
            stream.close()
        if audio: audio.terminate()
        # Сигналізуємо трею, що основний цикл завершено (якщо він ще працює)
        if tray_manager.is_running:
            tray_manager.stop() # Це зупинить іконку

if __name__ == "__main__":
    try:
        config = cfg.load_config() # Завантажуємо конфіг перед запуском
    except (FileNotFoundError, ValueError) as e:
         print(f"Не вдалося завантажити конфігурацію: {e}")
         # Тут можна показати вікно помилки, якщо це .exe без консолі
         exit() # Виходимо, якщо немає конфігу або ключа

    tray = TrayManager("Jarvis Assistant")
    # Передаємо функцію main_loop, яка буде запущена в окремому потоці
    tray.start(main_loop) 
    # Головний потік тепер заблокований викликом tray.start() (точніше, icon.run())
    # і чекатиме, доки користувач не натисне "Вихід"
    print("Програма завершена.") # Цей рядок виконається після закриття трею