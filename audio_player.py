# audio_player.py
import os
import sys
import winsound
from logger_config import get_logger
import pygame
import subprocess
import time
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

    def speak(self, text, voice_type="jarvis", rate="+10%"):
        """Синхронний TTS через subprocess (уникає конфлікти event loop)"""
        try:
            voice = self.voices.get(voice_type, 'uk-UA-OstapNeural')
            logger.info(f"Using Edge TTS voice: {voice} with rate: {rate}")

            # Створюємо тимчасовий файл
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_path = temp_file.name

            try:
                # Налаштування для приховання вікна консолі на Windows
                startupinfo = None
                if os.name == 'nt':
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0  # 0 = SW_HIDE

                # Запускаємо edge-tts через командний рядок з параметром швидкості
                cmd = [
                    'python', '-m', 'edge_tts',
                    '--voice', voice,
                    '--rate', rate,
                    '--text', text,
                    '--write-media', temp_path
                ]

                # Виконуємо команду з переданим startupinfo
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=10,
                    startupinfo=startupinfo, # <--- Додано цей параметр
                    creationflags=0x08000000 if os.name == 'nt' else 0 # <--- Додатковий захист (CREATE_NO_WINDOW)
                )

                if result.returncode == 0:
                    # Відтворюємо файл
                    print(f"[TTS] music.load + play: {text[:40]!r}")
                    pygame.mixer.music.load(temp_path)
                    pygame.mixer.music.play()

                    # Чекаємо поки закінчиться відтворення
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)

                    print(f"[TTS] done playing: {text[:40]!r}")
                    logger.debug(f"Edge TTS played: {text[:50]}...")
                    return True
                else:
                    logger.error(f"Edge TTS command failed: {result.stderr}")
                    print(f"[TTS] subprocess failed (rc={result.returncode}): {result.stderr[:100]}")
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



class TTSManager:
    """Менеджер для текстового мовлення (TTS) з використанням Edge TTS"""

    def __init__(self):
        self.edge_tts = EdgeTTS()

    def speak(self, text, voice_type="jarvis", rate="+10%"):
        """Промовляє текст через Edge TTS"""
        if not text:
            return False

        try:
            # Очищуємо текст від спеціальних символів для кращого звучання
            clean_text = text.replace("✅", "").replace("❌", "").replace("⚠️", "").strip()

            if not clean_text:
                return False

            logger.debug(f"Speaking: {clean_text[:50]}...")
            return self.edge_tts.speak(clean_text, voice_type=voice_type, rate=rate)

        except Exception as e:
            logger.error(f"Failed to speak text: {e}")
            return False

    def is_available(self):
        """Перевіряє чи доступний TTS движок"""
        return True  # Edge TTS завжди доступний

    def stop(self):
        """Зупиняє поточне мовлення"""
        try:
            pygame.mixer.music.stop()
            logger.debug("TTS stopped")
        except Exception as e:
            logger.error(f"Failed to stop TTS: {e}")

# Глобальні екземпляри TTS
_tts_manager = None
_edge_tts = None

def get_tts_manager():
    """Отримує глобальний екземпляр TTS менеджера"""
    global _tts_manager
    if _tts_manager is None:
        _tts_manager = TTSManager()
    return _tts_manager

def get_edge_tts():
    """Отримує глобальний екземпляр Edge TTS"""
    global _edge_tts
    if _edge_tts is None:
        _edge_tts = EdgeTTS()
    return _edge_tts

def get_voice_by_wake_word(config):
    """Визначає голос на основі wake word"""
    wake_word_mode = config.get("wakeWordMode", "standard")

    if wake_word_mode == "standard":
        wake_word = config.get("wakeWordStandard", "alexa").lower()

        if wake_word == "jarvis":
            return "jarvis"  # Чоловічий голос (Ostap)
        elif wake_word == "alexa":
            return "polina"  # Жіночий голос (Polina)
        else:
            # Для інших wake words використовуємо налаштування
            return config.get("ttsVoice", "jarvis")
    else:
        # Для custom wake word використовуємо налаштування з конфігу
        return config.get("ttsVoice", "jarvis")

def speak_text(text, config=None):
    """Швидка функція для мовлення тексту з конфігурацією через Edge TTS"""
    if not config:
        return False

    # Перевіряємо чи увімкнений TTS
    if not config.get("ttsEnabled", False):
        return False

    # Використовуємо Edge TTS (найкращий для української)
    edge_tts = get_edge_tts()

    # Автоматично вибираємо голос за wake word
    voice_type = get_voice_by_wake_word(config)

    # Швидкість мовлення
    rate = config.get("ttsRate", "+10%")

    logger.info(f"Using Edge TTS for: '{text[:50]}...' with voice: {voice_type}, rate: {rate}")
    return edge_tts.speak(text, voice_type=voice_type, rate=rate)


def play_jarvis_greeting(config):
    """Програє Jarvis вітальну фразу замість звуку при ttsEnabled: true"""
    import random

    greetings = [
        "Так, сер",
        "Я вас слухаю, сер",
        "На вашу послугу, сер",
        "Слухаю вас, сер",
        "Як завжди, сер"
    ]

    greeting = random.choice(greetings)
    speak_text(greeting, config)


def handle_wake_word_response(config):
    """Розумно обирає звук або TTS залежно від налаштувань"""
    if config.get("ttsEnabled", False):
        # Якщо TTS увімкнений - говорити Jarvis фразу
        play_jarvis_greeting(config)
    else:
        # Якщо TTS вимкнений - грати звук
        play_listen_sound()


def handle_session_end(config):
    """Обробляє завершення сесії - тільки звук якщо TTS вимкнений"""
    if not config.get("ttsEnabled", False):
        # Звук тільки якщо TTS вимкнений
        play_end_sound()
    # Якщо TTS увімкнений - тиша при завершенні