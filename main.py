import time
import struct
import pyaudio
import pvporcupine
import threading
from wake_word import WakeWordHandler
from tray_manager import TrayManager
import config_manager as cfg
import settings

def listen_loop(tray_manager, handler, porcupine, stream, config):
    """Основний цикл, що виконується в окремому потоці."""
    print(f"🎤 Слухаю '{config['wakeWordStandard']}'...")
    while tray_manager.is_running:
        try:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            audio_data = struct.unpack_from("h" * porcupine.frame_length, pcm)
            keyword_index = porcupine.process(audio_data)

            if keyword_index >= 0:
                handler.on_wake_word_detected(config["wakeWordStandard"])

        except (IOError, OSError) as e:
            if tray_manager.is_running:
                print(f"⚠️ Помилка читання аудіо: {e}. Спробуємо продовжити.")
            time.sleep(1)
        except Exception as e:
            if tray_manager.is_running:
                print(f"❌ Неочікувана помилка в циклі слухання: {e}")
            break

def main():
    """Головна функція: ініціалізація та очищення."""
    config = None
    tray = None
    porcupine = None
    audio = None
    stream = None

    try:
        config = cfg.load_config()
        tray = TrayManager("Jarvis Assistant")
        handler = WakeWordHandler(tray)
        
        porcupine = pvporcupine.create(
            access_key=config["picovoiceAccessKey"],
            keywords=[config["wakeWordStandard"]],
            sensitivities=[config["sensitivity"]]
        )
        print(f"✅ Модель Porcupine '{config['wakeWordStandard']}' завантажена")

        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=settings.FORMAT,
            channels=settings.CHANNELS,
            rate=porcupine.sample_rate,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )

        listen_thread = threading.Thread(
            target=listen_loop,
            args=(tray, handler, porcupine, stream, config),
            daemon=True
        )
        listen_thread.start()

        print("✅ Асистент запущено у фоновому режимі.")
        tray.start()

    except Exception as e:
        print(f"❌ Критична помилка під час запуску: {e}")
    finally:
        print("\n--- Завершення роботи та очищення ресурсів ---")
        if tray:
            tray.stop()
        if porcupine:
            porcupine.delete()
        if stream:
            stream.stop_stream()
            stream.close()
        if audio:
            audio.terminate()
        print("✅ Програма завершена.")

if __name__ == "__main__":
    main()