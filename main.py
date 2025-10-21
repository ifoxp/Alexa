# main.py
import pyaudio
import struct
import pvporcupine
import time
from wake_word import WakeWordHandler
import settings

def main():
    if not settings.PICOVOICE_ACCESS_KEY or "ПАСТА_СЮДИ" in settings.PICOVOICE_ACCESS_KEY:
        print("❌ Помилка: Будь ласка, вставте ваш PICOVOICE_ACCESS_KEY у файл settings.py")
        return

    print("Ініціалізація системи розпізнавання wake word (Porcupine)...")

    try:
        porcupine = pvporcupine.create(
            access_key=settings.PICOVOICE_ACCESS_KEY,
            keywords=settings.WAKE_WORD_MODELS,
            sensitivities=[settings.ACTIVATION_THRESHOLD] * len(settings.WAKE_WORD_MODELS)
        )
        print(f"✅ Моделі Porcupine {settings.WAKE_WORD_MODELS} завантажені")
    except Exception as e:
        print(f"❌ Не вдалося завантажити моделі Porcupine: {e}")
        return

    audio = pyaudio.PyAudio()
    # Створюємо handler без передачі audio та params, оскільки OnlineTranscriber їх не потребує
    handler = WakeWordHandler()

    stream = None # Initialize stream to None
    try:
        stream = audio.open(
            format=settings.FORMAT,
            channels=settings.CHANNELS,
            rate=porcupine.sample_rate,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )
        print(f"🎤 Слухаю wake word(s): {settings.WAKE_WORD_MODELS}... (Натисніть Ctrl+C для зупинки)")

        while True:
            pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
            audio_data = struct.unpack_from("h" * porcupine.frame_length, pcm)
            keyword_index = porcupine.process(audio_data)

            if keyword_index >= 0:
                detected_keyword = settings.WAKE_WORD_MODELS[keyword_index]
                # У цьому простому варіанті ми не зупиняємо потік Porcupine,
                # бо OnlineTranscriber відкриє свій власний потік.
                handler.on_wake_word_detected(detected_keyword)

    except KeyboardInterrupt:
        print("\n⏹️ Зупинка програми...")
    except Exception as e:
        print(f"❌ Помилка: {e}")
    finally:
        if 'porcupine' in locals():
            porcupine.delete()
        if stream is not None and stream.is_active():
            stream.stop_stream()
            stream.close()
        if 'audio' in locals():
            audio.terminate()
        print("✅ Програма завершена")

if __name__ == "__main__":
    main()