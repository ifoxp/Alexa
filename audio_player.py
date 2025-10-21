# audio_player.py
import os
import sys
import winsound # <-- ВИКОРИСТОВУЄМО ВБУДОВАНУ БІБЛІОТЕКУ
import threading

def get_asset_path(filename):
    """Визначає правильний шлях до файлу в папці assets."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, "assets", filename)

def play_sound(sound_name):
    """Програє звук за допомогою winsound."""
    try:
        path = get_asset_path(sound_name)
        if os.path.exists(path):
            # winsound.SND_ASYNC програє звук у фоні, не блокуючи програму
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            print(f"⚠️ Аудіофайл не знайдено: {path}")
    except Exception as e:
        print(f"❌ Помилка при програванні звуку {sound_name}: {e}")

def play_listen_sound():
    play_sound("listen.wav")

def play_end_sound():
    play_sound("end.wav")