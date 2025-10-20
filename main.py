import pyaudio
import numpy as np
from openwakeword.model import Model
import argparse
import time
from wake_word import WakeWordHandler

def main():
    print("Ініціалізація системи розпізнавання wake word...")

    # Налаштування аудіо
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    CHUNK = 1280  # 80ms chunks at 16kHz

    # Ініціалізація моделі openWakeWord з використанням доступних моделей
    try:
        # Спробуємо використати вбудовану модель "alexa"
        owwModel = Model(wakeword_models=["alexa"])
        print("✅ Модель 'alexa' завантажена")
    except:
        try:
            # Якщо alexa недоступна, використаємо hey_jarvis як альтернативу
            owwModel = Model(wakeword_models=["hey_jarvis"])
            print("✅ Модель 'hey_jarvis' завантажена (використовуйте 'Hey Jarvis' замість 'Alexa')")
        except:
            # Якщо жодна модель недоступна, завантажимо всі доступні
            owwModel = Model()
            print("✅ Завантажено всі доступні моделі")
            print("Доступні wake words:", list(owwModel.models.keys()))

    # Ініціалізація обробника wake word
    handler = WakeWordHandler()

    # Ініціалізація PyAudio
    audio = pyaudio.PyAudio()

    try:
        # Відкриття аудіо потоку
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )

        print(f"🎤 Слухаю wake word(s): {list(owwModel.models.keys())}... (Натисніть Ctrl+C для зупинки)")

        while True:
            # Читання аудіо даних
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)

            # Обробка через openWakeWord
            prediction = owwModel.predict(audio_data)

            # Перевірка на активацію wake word
            for mdl in owwModel.prediction_buffer.keys():
                scores = list(owwModel.prediction_buffer[mdl])
                if scores:
                    current_score = scores[-1]
                    if current_score > 0.7:  # Підвищений поріг активації
                        handler.on_wake_word_detected(mdl, current_score)

    except KeyboardInterrupt:
        print("\n⏹️ Зупинка програми...")

    except Exception as e:
        print(f"❌ Помилка: {e}")

    finally:
        # Закриття ресурсів
        if 'stream' in locals():
            stream.stop_stream()
            stream.close()
        audio.terminate()
        print("✅ Програма завершена")

if __name__ == "__main__":
    main()