# audio_player.py
import os
import sys
import winsound

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