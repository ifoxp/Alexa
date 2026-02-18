# audio_player.py
import os
import sys
import winsound
import win32com.client
from logger_config import get_logger
import requests
import pygame
import io
from urllib.parse import quote

logger = get_logger('audio_player')

def get_asset_path(filename):
    """Визначає правильний шлях до файлу в папці assets."""
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, "assets", filename)

def play_sound(sound_name):
    """Програє звук за допомогою winsound."""
    try:
        path = get_asset_path(sound_name)
        if os.path.exists(path):
            # SND_ASYNC програє у фоні
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            print(f"⚠️ Аудіофайл не знайдено: {path}")
    except Exception as e:
        print(f"❌ Помилка при програванні звуку {sound_name}: {e}")

def play_listen_sound():
    play_sound("listen.wav")

def play_end_sound():
    play_sound("end.wav")

class GoogleTTS:
    """Клас для роботи з Google Text-to-Speech"""

    def __init__(self):
        pygame.mixer.init()
        self.base_url = "https://translate.google.com/translate_tts"

    def speak(self, text, language="uk", slow=False):
        """Озвучує текст через Google TTS"""
        try:
            if not text.strip():
                return False

            # Параметри для Google TTS API
            params = {
                'ie': 'UTF-8',
                'q': text,
                'tl': language,  # uk = українська
                'client': 'tw-ob',
                'ttsspeed': 0.8 if slow else 1.0
            }

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            # Робимо запит до Google TTS
            response = requests.get(self.base_url, params=params, headers=headers, timeout=5)

            if response.status_code == 200:
                # Відтворюємо аудіо через pygame
                audio_data = io.BytesIO(response.content)
                pygame.mixer.music.load(audio_data)
                pygame.mixer.music.play()

                # Чекаємо поки закінчиться відтворення
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)

                logger.debug(f"Google TTS played: {text[:50]}...")
                return True
            else:
                logger.error(f"Google TTS failed with status: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Google TTS error: {e}")
            return False

class TTSManager:
    """Менеджер для текстового мовлення (TTS)"""

    def __init__(self):
        self.engine = None
        self.voices = {}
        self._initialize_engine()

    def _initialize_engine(self):
        """Ініціалізація TTS движка Windows SAPI"""
        try:
            self.engine = win32com.client.Dispatch("SAPI.SpVoice")

            # Завантажуємо доступні голоси
            voices = self.engine.GetVoices()
            for i in range(voices.Count):
                voice = voices.Item(i)
                voice_name = voice.GetDescription()
                self.voices[voice_name.lower()] = i
                logger.info(f"Available voice: {voice_name}")  # Змінено на INFO щоб бачити в логах

            # Налаштовуємо параметри за замовчуванням для більш живого звучання
            self.engine.Rate = 1  # Трохи швидше для більш живого звучання
            self.engine.Volume = 85  # Трохи тихіше щоб не кричало

            logger.info("TTS engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize TTS engine: {e}")
            self.engine = None

    def set_voice(self, voice_type="jarvis"):
        """Встановлює голос на основі типу"""
        if not self.engine:
            return False

        try:
            # Пошук голосу для Jarvis-подібного звучання
            preferred_voices = []

            if voice_type.lower() == "jarvis":
                # Шукаємо українські/російські голоси у порядку пріоритету
                preferred_voices = [
                    "microsoft ostap",     # Український чоловічий (якщо встановлений)
                    "ostap",
                    "microsoft natalia",   # Українська жіноча (якщо встановлена)
                    "natalia",
                    "microsoft pavel",     # Російський чоловічий
                    "pavel",
                    "microsoft irina",     # Російська жіноча
                    "irina",
                    "microsoft katya",     # Російська жіноча
                    "katya",
                    "microsoft david",     # Англійський як останній варіант
                    "david"
                ]

            # Шукаємо найбільш підходящий голос
            for preferred in preferred_voices:
                for voice_name, voice_index in self.voices.items():
                    if preferred in voice_name.lower():
                        voices = self.engine.GetVoices()
                        self.engine.Voice = voices.Item(voice_index)
                        logger.info(f"Voice set to: {voice_name}")
                        return True

            # Якщо не знайшли, використовуємо перший доступний
            if self.voices:
                voices = self.engine.GetVoices()
                self.engine.Voice = voices.Item(0)
                first_voice = list(self.voices.keys())[0]
                logger.info(f"Using fallback voice: {first_voice}")
                return True

        except Exception as e:
            logger.error(f"Failed to set voice: {e}")

        return False

    def set_speed(self, speed=0):
        """Встановлює швидкість мовлення (-10 до 10)"""
        if not self.engine:
            return False

        try:
            # Обмежуємо швидкість в допустимих межах
            speed = max(-10, min(10, speed))
            self.engine.Rate = speed
            logger.debug(f"TTS speed set to: {speed}")
            return True
        except Exception as e:
            logger.error(f"Failed to set TTS speed: {e}")
            return False

    def speak(self, text, async_mode=True):
        """Промовляє текст"""
        if not self.engine or not text:
            return False

        try:
            # Очищуємо текст від спеціальних символів для кращого звучання
            clean_text = text.replace("✅", "").replace("❌", "").replace("⚠️", "").strip()

            if not clean_text:
                return False

            # Режим синхронний (0) або асинхронний (1)
            flags = 1 if async_mode else 0

            logger.debug(f"Speaking: {clean_text[:50]}...")
            self.engine.Speak(clean_text, flags)
            return True

        except Exception as e:
            logger.error(f"Failed to speak text: {e}")
            return False

    def is_available(self):
        """Перевіряє чи доступний TTS движок"""
        return self.engine is not None

    def stop(self):
        """Зупиняє поточне мовлення"""
        if self.engine:
            try:
                self.engine.Skip("Sentence", 999999)
                logger.debug("TTS stopped")
            except Exception as e:
                logger.error(f"Failed to stop TTS: {e}")

# Глобальні екземпляри TTS
_tts_manager = None
_google_tts = None

def get_tts_manager():
    """Отримує глобальний екземпляр TTS менеджера"""
    global _tts_manager
    if _tts_manager is None:
        _tts_manager = TTSManager()
    return _tts_manager

def get_google_tts():
    """Отримує глобальний екземпляр Google TTS"""
    global _google_tts
    if _google_tts is None:
        _google_tts = GoogleTTS()
    return _google_tts

def speak_text(text, config=None):
    """Швидка функція для мовлення тексту з конфігурацією"""
    if not config:
        return False

    # Перевіряємо чи увімкнений TTS
    if not config.get("ttsEnabled", False):
        return False

    # Вибираємо TTS движок
    tts_engine = config.get("ttsEngine", "windows")  # windows або google

    if tts_engine == "google":
        # Використовуємо Google TTS
        google_tts = get_google_tts()
        language = config.get("ttsLanguage", "uk")
        slow_speech = config.get("ttsSpeed", 1) < 1

        logger.info(f"Using Google TTS for: '{text[:50]}...' in language: {language}")
        return google_tts.speak(text, language=language, slow=slow_speech)

    else:
        # Використовуємо Windows SAPI
        tts = get_tts_manager()
        if not tts.is_available():
            logger.warning("Windows TTS engine not available, fallback to Google TTS")
            google_tts = get_google_tts()
            return google_tts.speak(text, language="uk")

        # Налаштовуємо голос і швидкість
        voice_type = config.get("ttsVoice", "jarvis")
        speed = config.get("ttsSpeed", 0)

        tts.set_voice(voice_type)
        tts.set_speed(speed)

        return tts.speak(text)