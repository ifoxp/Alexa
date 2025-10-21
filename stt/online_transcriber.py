import speech_recognition as sr
import settings

class OnlineTranscriber:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone(
            sample_rate=settings.RATE,
            chunk_size=settings.CHUNK
        )
        self.current_language = settings.DEFAULT_LANGUAGE
        # Налаштовуємо один раз при старті
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

    def set_language(self, lang_code):
        self.current_language = lang_code
        print(f"Встановлено мову транскрипції: {lang_code}")

    def listen_and_transcribe(self, timeout):
        """Слухає одну фразу з динамічним таймаутом."""
        if not timeout or timeout <= 0:
            return None

        with self.microphone as source:
            self.recognizer.pause_threshold = settings.SILENCE_DETECT_SECONDS
            
            try:
                print(f" M... (залишилось {timeout:.1f}с)")
                audio = self.recognizer.listen(source, timeout=timeout)
            except sr.WaitTimeoutError:
                return None

        try:
            transcript = self.recognizer.recognize_google(
                audio, 
                language=self.current_language
            )
            return transcript
        except (sr.UnknownValueError, sr.RequestError):
            return None