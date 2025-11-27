import time
import struct
import pyaudio
import pvporcupine
import threading
import os
from wake_word import WakeWordHandler
from tray_manager import TrayManager
import config_manager as cfg
import settings

def listen_loop(tray_manager, handler, porcupine, stream, config):
    """
    Основний цикл, що виконується в окремому потоці.
    """
    # Визначаємо, яке слово слухаємо, для логування
    if config.get('wakeWordMode') == 'custom' and config.get('customWakeWordPath'):
        active_keyword = os.path.basename(config['customWakeWordPath'])
    else:
        active_keyword = config.get('wakeWordStandard', 'porcupine')

    print(f"🎤 Слухаю '{active_keyword}'...")
    while tray_manager.is_running:
        try:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            audio_data = struct.unpack_from("h" * porcupine.frame_length, pcm)
            keyword_index = porcupine.process(audio_data)

            if keyword_index >= 0:
                handler.on_wake_word_detected(active_keyword)

        except (IOError, OSError) as e:
            if tray_manager.is_running: print(f"⚠️ Помилка читання аудіо: {e}.")
            time.sleep(1)
        except Exception as e:
            if tray_manager.is_running: print(f"❌ Неочікувана помилка в циклі слухання: {e}")
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
        
        # --- ОНОВЛЕНА ЛОГІКА ІНІЦІАЛІЗАЦІЇ PORCUPINE ---
        porcupine_kwargs = {
            'access_key': config["picovoiceAccessKey"],
            'sensitivities': [config["sensitivity"]]
        }

        # Перевіряємо режим роботи з конфігу
        if config.get("wakeWordMode") == "custom":
            custom_path = config.get("customWakeWordPath")
            if not custom_path or not os.path.exists(custom_path):
                print(f"⚠️ Кастомна модель не знайдена: {custom_path}")
                print("📋 Fallback до стандартної моделі...")
                # Fallback до стандартної моделі
                standard_keyword = config.get("wakeWordStandard", "alexa")
                porcupine_kwargs['keywords'] = [standard_keyword]
                print(f"✅ Використовується стандартна модель: '{standard_keyword}'")
            else:
                porcupine_kwargs['keyword_paths'] = [custom_path]
                print(f"✅ Використовується кастомна модель: {os.path.basename(custom_path)}")

        else: # 'standard' mode (за замовчуванням)
            standard_keyword = config.get("wakeWordStandard", "alexa")
            porcupine_kwargs['keywords'] = [standard_keyword]
            print(f"✅ Використовується стандартна модель: '{standard_keyword}'")

        porcupine = pvporcupine.create(**porcupine_kwargs)
        # ---------------------------------------------
        
        handler = WakeWordHandler(tray)
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
        if tray: tray.stop()
        if porcupine: porcupine.delete()
        if stream:
            try:
                if stream.is_active():
                    stream.stop_stream()
                stream.close()
            except Exception: pass # Ігноруємо помилки при закритті
        if audio: audio.terminate()
        print("✅ Програма завершена.")

if __name__ == "__main__":
    main()