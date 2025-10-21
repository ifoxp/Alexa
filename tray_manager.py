# tray_manager.py
import pystray
from PIL import Image, ImageOps
import threading
import sys
import os

def get_asset_path(filename):
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, "assets", filename)

def _colorize_icon(image, target_color=(0, 255, 0, 255)): # Зелений колір RGBA
    """Перефарбовує білі (або майже білі) пікселі іконки."""
    img = image.convert("RGBA")
    data = img.getdata()
    newData = []
    threshold = 200 # Наскільки "білим" має бути піксель, щоб його перефарбувати
    
    for item in data:
        # Перевіряємо, чи піксель достатньо білий і не повністю прозорий
        if item[0] > threshold and item[1] > threshold and item[2] > threshold and item[3] > 0:
            # Замінюємо на цільовий колір, зберігаючи прозорість оригіналу (або роблячи непрозорим)
            newData.append(target_color) 
        else:
            newData.append(item) # Залишаємо оригінальний піксель
            
    img.putdata(newData)
    return img

class TrayManager:
    def __init__(self, app_name="Голосовий Асистент"):
        self.app_name = app_name
        self.icon_default_path = get_asset_path("ai.png")
        self.icon_default = Image.open(self.icon_default_path)
        self.icon_listening = _colorize_icon(self.icon_default) # Генеруємо зелену іконку
        self.icon_instance = None
        self.is_running = True
        self.main_app_thread = None

    def _on_settings(self, icon, item):
        print("Запуск налаштувань...")
        try:
            base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else "."
            settings_exe_path = os.path.join(base_path, "Configurator.exe") # Припускаємо назву C# додатку
            if os.path.exists(settings_exe_path):
                os.startfile(settings_exe_path)
            else:
                print(f"❌ Не знайдено файл налаштувань: {settings_exe_path}")
        except Exception as e:
            print(f"❌ Помилка при запуску налаштувань: {e}")

    def _on_exit(self, icon, item):
        print("Завершення роботи...")
        self.is_running = False
        if self.icon_instance:
            self.icon_instance.stop()

    def _run_icon(self, main_loop_func):
        menu = pystray.Menu(
            pystray.MenuItem('Налаштування', self._on_settings),
            pystray.MenuItem('Вихід', self._on_exit)
        )
        self.icon_instance = pystray.Icon(self.app_name, self.icon_default, self.app_name, menu)
        
        self.main_app_thread = threading.Thread(target=main_loop_func, args=(self,), daemon=True)
        self.main_app_thread.start()

        self.icon_instance.run() # Цей виклик блокує головний потік

    def start(self, main_loop_func):
        self._run_icon(main_loop_func)

    def set_icon_state(self, is_listening):
        """Змінює іконку (біла/зелена)."""
        if self.icon_instance:
            new_icon = self.icon_listening if is_listening else self.icon_default
            self.icon_instance.icon = new_icon