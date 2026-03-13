import time
import struct
import pyaudio
import pvporcupine
import threading
import os
from functools import lru_cache
from wake_word import WakeWordHandler
from tray_manager import TrayManager
import config_manager as cfg
import settings
from logger_config import get_logger
from audio_buffer import BufferedAudioStream
from memory_manager import memory_manager, ResourceManager, log_memory_usage
import smart_ai

logger = get_logger('main')

@lru_cache(maxsize=3)
def create_porcupine_model(access_key, model_path, sensitivity, is_custom):
    """Створює Porcupine модель з кешуванням."""
    cache_key = f"{model_path}_{sensitivity}" if is_custom else f"{model_path}_{sensitivity}"

    logger.info("Creating porcupine model", extra={
        'model_path': model_path,
        'sensitivity': sensitivity,
        'is_custom': is_custom,
        'cache_key': cache_key
    })

    if is_custom:
        return pvporcupine.create(
            access_key=access_key,
            keyword_paths=[model_path],
            sensitivities=[sensitivity]
        )
    else:
        return pvporcupine.create(
            access_key=access_key,
            keywords=[model_path],  # model_path містить назву ключового слова
            sensitivities=[sensitivity]
        )

def get_microphone_index(audio_instance, device_name: str):
    """
    Повертає індекс мікрофону за його назвою.
    Якщо назва порожня або не знайдена — повертає None (системний за замовчуванням).
    """
    if not device_name:
        return None
    count = audio_instance.get_device_count()
    for i in range(count):
        info = audio_instance.get_device_info_by_index(i)
        if info.get('maxInputChannels', 0) > 0 and device_name.lower() in info['name'].lower():
            logger.info("Знайдено мікрофон", extra={'index': i, 'device_name': info['name']})
            return i
    logger.warning("Мікрофон не знайдено, використовую системний", extra={'requested': device_name})
    return None


def listen_loop(tray_manager, handler, porcupine, buffered_stream, config):
    """
    Основний цикл, що виконується в окремому потоці з буферизованим потоком.
    """
    # Визначаємо, яке слово слухаємо, для логування
    if config.get('wakeWordMode') == 'custom' and config.get('customWakeWordPath'):
        active_keyword = os.path.basename(config['customWakeWordPath'])
    else:
        active_keyword = config.get('wakeWordStandard', 'porcupine')

    logger.info(f"Слухаю '{active_keyword}'...", extra={'wake_word': active_keyword})

    while tray_manager.is_running:
        try:
            # Читаємо з буферизованого потоку
            audio_data = buffered_stream.read_frame(porcupine.frame_length, timeout=1.0)

            if audio_data and len(audio_data) == porcupine.frame_length:
                keyword_index = porcupine.process(audio_data)

                if keyword_index >= 0:
                    logger.info("Wake word detected", extra={
                        'wake_word': active_keyword,
                        'keyword_index': keyword_index,
                        'buffer_stats': buffered_stream.get_buffer_stats()
                    })
                    handler.on_wake_word_detected(active_keyword)
            elif audio_data is None:
                # Таймаут читання - це нормально
                continue
            else:
                logger.debug("Incomplete audio frame", extra={
                    'expected': porcupine.frame_length,
                    'got': len(audio_data) if audio_data else 0
                })

        except Exception as e:
            if tray_manager.is_running:
                logger.error("Unexpected error in listen loop", extra={
                    'error': str(e),
                    'error_type': type(e).__name__
                })
                time.sleep(0.1)  # Коротка пауза перед повторною спробою
            else:
                break

    logger.info("Listen loop terminated")

@log_memory_usage("main_function")
def main():
    """Головна функція: ініціалізація та очищення."""
    logger.info("Starting assistant initialization")

    with ResourceManager(memory_manager) as resource_mgr:
        config = None
        tray = None
        porcupine = None
        audio = None
        buffered_stream = None

        try:
            config = cfg.load_config()
            tray = resource_mgr.add(TrayManager("Jarvis Assistant"))

            # --- ІНІЦІАЛІЗАЦІЯ ШІ АСИСТЕНТА ---
            openai_key = config.get("openaiApiKey", "").strip()

            if openai_key and openai_key != "YOUR_OPENAI_API_KEY_HERE":
                if smart_ai.initialize_smart_assistant(openai_key):
                    logger.info("Smart AI assistant enabled")
                    # Прогріваємо плагіни при старті щоб перша команда не мала затримки
                    try:
                        from smart_plugin_manager import SmartPluginManager
                        smart_ai.smart_assistant.plugin_manager = SmartPluginManager()
                        logger.info("Plugin manager pre-initialized at startup")
                    except Exception as e:
                        logger.warning("Plugin manager pre-init failed", extra={'error': str(e)})
                else:
                    logger.warning("Failed to initialize AI assistant")
            else:
                logger.info("OpenAI API key not set — AI assistant disabled")

            # --- ОНОВЛЕНА ЛОГІКА ІНІЦІАЛІЗАЦІЇ PORCUPINE З КЕШЕМ ---
            access_key = config["picovoiceAccessKey"]
            sensitivity = config["sensitivity"]

            # Перевіряємо режим роботи з конфігу
            if config.get("wakeWordMode") == "custom":
                custom_path = config.get("customWakeWordPath")
                if not custom_path or not os.path.exists(custom_path):
                    logger.warning("Custom wake word model not found", extra={
                        'custom_path': custom_path,
                        'fallback': 'standard_model'
                    })
                    # Fallback до стандартної моделі
                    standard_keyword = config.get("wakeWordStandard", "alexa")
                    porcupine = create_porcupine_model(
                        access_key=access_key,
                        model_path=standard_keyword,
                        sensitivity=sensitivity,
                        is_custom=False
                    )
                    logger.info("Using cached standard wake word model", extra={
                        'model': standard_keyword,
                        'type': 'fallback'
                    })
                else:
                    porcupine = create_porcupine_model(
                        access_key=access_key,
                        model_path=custom_path,
                        sensitivity=sensitivity,
                        is_custom=True
                    )
                    logger.info("Using cached custom wake word model", extra={
                        'model_path': custom_path,
                        'model_name': os.path.basename(custom_path),
                        'type': 'custom'
                    })
            else: # 'standard' mode (за замовчуванням)
                standard_keyword = config.get("wakeWordStandard", "alexa")
                porcupine = create_porcupine_model(
                    access_key=access_key,
                    model_path=standard_keyword,
                    sensitivity=sensitivity,
                    is_custom=False
                )
                logger.info("Using cached standard wake word model", extra={
                    'model': standard_keyword,
                    'type': 'standard'
                })
        # ---------------------------------------------
        
            # Створюємо handler та аудіо ресурси
            handler = WakeWordHandler(tray)
            audio = resource_mgr.add(pyaudio.PyAudio())

            # Визначаємо індекс мікрофону з конфігу
            mic_device_name = config.get("microphoneDevice", "")
            mic_index = get_microphone_index(audio, mic_device_name)

            logger.info("Аудіо пристрій", extra={
                'microphoneDevice': mic_device_name or '(системний за замовчуванням)',
                'input_device_index': mic_index
            })

            # Створюємо звичайний stream
            raw_stream = audio.open(
                format=settings.FORMAT,
                channels=settings.CHANNELS,
                rate=porcupine.sample_rate,
                input=True,
                input_device_index=mic_index,
                frames_per_buffer=512
            )

            # Обгортаємо в буферизований stream
            buffered_stream = resource_mgr.add(
                BufferedAudioStream(raw_stream, buffer_size=8192),
                cleanup_func=lambda s: s.close()
            )

            # Запускаємо буферизацію
            buffered_stream.start_buffering()

            logger.info("Audio system initialized", extra={
                'sample_rate': porcupine.sample_rate,
                'buffer_size': 8192
            })

            # Запускаємо listen loop з буферизованим потоком
            listen_thread = threading.Thread(
                target=listen_loop,
                args=(tray, handler, porcupine, buffered_stream, config),
                daemon=True
            )
            listen_thread.start()

            logger.info("Assistant started successfully")
            tray.start()

        except Exception as e:
            logger.error("Critical startup error", extra={
                'error': str(e),
                'error_type': type(e).__name__
            })
        finally:
            logger.info("Starting cleanup and resource shutdown")
            if tray: tray.stop()
            if porcupine: porcupine.delete()
            if buffered_stream:
                try:
                    buffered_stream.close()
                except Exception as cleanup_error:
                    logger.debug("Stream cleanup error", extra={'error': str(cleanup_error)})
            if audio: audio.terminate()
            logger.info("Program terminated successfully")

if __name__ == "__main__":
    main()