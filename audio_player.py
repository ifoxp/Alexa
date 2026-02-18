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
import asyncio
import edge_tts
import subprocess
import tempfile

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

class EdgeTTS:
    """Клас для роботи з Microsoft Edge TTS (найкращий безкоштовний український Джарвіс-голос)"""

    def __init__(self):
        pygame.mixer.init()
        # Ostap - чоловічий український голос, Polina - жіночий
        self.voices = {
            'jarvis': 'uk-UA-OstapNeural',      # Чоловічий український (як Джарвіс)
            'polina': 'uk-UA-PolinaNeural',     # Жіночий український
            'ostap': 'uk-UA-OstapNeural'        # Чоловічий український (альтернативна назва)
        }

    def speak(self, text, voice_type="jarvis"):
        """Синхронний TTS через subprocess (уникає конфлікти event loop)"""
        try:
            voice = self.voices.get(voice_type, 'uk-UA-OstapNeural')
            logger.info(f"Using Edge TTS voice: {voice}")

            # Створюємо тимчасовий файл
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_path = temp_file.name

            try:
                # Запускаємо edge-tts через командний рядок
                cmd = [
                    'python', '-m', 'edge_tts',
                    '--voice', voice,
                    '--text', text,
                    '--write-media', temp_path
                ]

                # Виконуємо команду
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

                if result.returncode == 0:
                    # Відтворюємо файл
                    pygame.mixer.music.load(temp_path)
                    pygame.mixer.music.play()

                    # Чекаємо поки закінчиться відтворення
                    while pygame.mixer.music.get_busy():
                        pygame.time.Clock().tick(10)

                    logger.debug(f"Edge TTS played: {text[:50]}...")
                    return True
                else:
                    logger.error(f"Edge TTS command failed: {result.stderr}")
                    return False

            finally:
                # Видаляємо тимчасовий файл
                try:
                    os.unlink(temp_path)
                except:
                    pass

        except Exception as e:
            logger.error(f"Edge TTS error: {e}")
            return False

class ElevenLabsTTS:
    """Клас для роботи з ElevenLabs TTS (преміум якість)"""

    def __init__(self, api_key=None):
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io/v1/text-to-speech"
        # Jarvis-подібний голос ID (треба буде налаштувати)
        self.voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel (англійська)
        pygame.mixer.init()

    def speak(self, text, voice_id=None):
        """Озвучує текст через ElevenLabs"""
        if not self.api_key:
            logger.warning("ElevenLabs API key not provided")
            return False

        try:
            voice_id = voice_id or self.voice_id
            url = f"{self.base_url}/{voice_id}"

            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }

            data = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.5,
                    "style": 0.5,
                    "use_speaker_boost": True
                }
            }

            response = requests.post(url, json=data, headers=headers, timeout=10)

            if response.status_code == 200:
                # Відтворюємо через pygame
                audio_data = io.BytesIO(response.content)
                pygame.mixer.music.load(audio_data)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    pygame.time.wait(100)

                logger.debug(f"ElevenLabs TTS played: {text[:50]}...")
                return True
            else:
                logger.error(f"ElevenLabs failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            return False

class GoogleTTS:
    """Клас для роботи з Google Text-to-Speech"""

    def __init__(self):
        pygame.mixer.init()
        self.base_url = "https://translate.google.com/translate_tts"

    def speak(self, text, language="uk", slow=False, try_male=True):
        """Озвучує текст через Google TTS"""
        try:
            if not text.strip():
                return False

            # Спробуємо різні варіанти для отримання чоловічого українського голосу
            voice_attempts = [
                {
                    'ie': 'UTF-8',
                    'q': text,
                    'tl': language,
                    'client': 'tw-ob',
                    'ttsspeed': 0.8,
                    'idx': 0,  # Перший голос (часто чоловічий)
                },
                {
                    'ie': 'UTF-8',
                    'q': text,
                    'tl': language,
                    'client': 'gtx',  # Альтернативний клієнт
                    'ttsspeed': 0.8,
                },
                {
                    'ie': 'UTF-8',
                    'q': text,
                    'tl': language,
                    'client': 'tw-ob',
                    'ttsspeed': 0.8,
                    'tk': '1',  # Додатковий параметр
                }
            ]

            # Пробуємо кожен варіант
            for attempt_num, params in enumerate(voice_attempts):
                try:
                    response = self._make_tts_request(params)
                    if response:
                        logger.info(f"Ukrainian TTS success with attempt #{attempt_num + 1}")
                        return response
                except Exception as e:
                    logger.debug(f"TTS attempt #{attempt_num + 1} failed: {e}")
                    continue

            return False

        except Exception as e:
            logger.error(f"Google TTS error: {e}")
            return False

    def _make_tts_request(self, params):
        """Допоміжна функція для TTS запиту"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(self.base_url, params=params, headers=headers, timeout=5)

        if response.status_code == 200:
            # Відтворюємо аудіо через pygame
            audio_data = io.BytesIO(response.content)
            pygame.mixer.music.load(audio_data)
            pygame.mixer.music.play()

            # Чекаємо поки закінчиться відтворення
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)

            return True

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
_edge_tts = None

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

def get_edge_tts():
    """Отримує глобальний екземпляр Edge TTS"""
    global _edge_tts
    if _edge_tts is None:
        _edge_tts = EdgeTTS()
    return _edge_tts

def speak_text(text, config=None):
    """Швидка функція для мовлення тексту з конфігурацією"""
    if not config:
        return False

    # Перевіряємо чи увімкнений TTS
    if not config.get("ttsEnabled", False):
        return False

    # Вибираємо TTS движок
    tts_engine = config.get("ttsEngine", "edge")  # edge, google, windows

    if tts_engine == "edge":
        # Використовуємо Edge TTS (найкращий для української)
        edge_tts = get_edge_tts()
        voice_type = config.get("ttsVoice", "jarvis")

        logger.info(f"Using Edge TTS for: '{text[:50]}...' with voice: {voice_type}")
        return edge_tts.speak(text, voice_type=voice_type)

    elif tts_engine == "google":
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
            logger.warning("Windows TTS engine not available, fallback to Edge TTS")
            edge_tts = get_edge_tts()
            return edge_tts.speak(text, voice_type="jarvis")

        # Налаштовуємо голос і швидкість
        voice_type = config.get("ttsVoice", "jarvis")
        speed = config.get("ttsSpeed", 0)

        tts.set_voice(voice_type)
        tts.set_speed(speed)

        return tts.speak(text)