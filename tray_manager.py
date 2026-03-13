# tray_manager.py
import pystray
from PIL import Image
import sys
import os

def get_asset_path(filename):
    # ... (код без змін) ...
    base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
    return os.path.join(base_path, "assets", filename)

def _colorize_icon(image, target_color=(0, 255, 0, 255)):
    # ... (код без змін) ...
    img = image.convert("RGBA")
    data = img.getdata()
    newData = []
    threshold = 200
    for item in data:
        if item[0] > threshold and item[1] > threshold and item[2] > threshold and item[3] > 0:
            newData.append(target_color)
        else:
            newData.append(item)
    img.putdata(newData)
    return img

class TrayManager:
    def __init__(self, app_name="Голосовий Асистент"):
        self.app_name = app_name
        self.icon_default = Image.open(get_asset_path("ai.png"))
        self.icon_listening = _colorize_icon(self.icon_default)
        self.icon_instance = None
        self.is_running = True

    def _on_settings(self, icon, item):
        # ... (код без змін) ...
        print("Запуск налаштувань...")
        try:
            base_path = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else "."
            settings_exe_path = os.path.join(base_path, "AlexaSettings.exe")
            if os.path.exists(settings_exe_path):
                os.startfile(settings_exe_path)
            else:
                print(f"❌ Не знайдено файл налаштувань: {settings_exe_path}")
        except Exception as e:
            print(f"❌ Помилка при запуску налаштувань: {e}")

    def _on_exit(self, icon, item):
        self.stop()

    def start(self):
        """Створює іконку і блокує потік до виходу."""
        menu = pystray.Menu(
            pystray.MenuItem('Налаштування', self._on_settings),
            pystray.MenuItem('Вихід', self._on_exit)
        )
        self.icon_instance = pystray.Icon(self.app_name, self.icon_default, self.app_name, menu)
        self.icon_instance.run()

    def stop(self):
        """Зупиняє іконку та сигналізує про завершення роботи."""
        if self.is_running:
            print("Сигнал на зупинку...")
            self.is_running = False
            if self.icon_instance:
                self.icon_instance.stop()

    def set_icon_state(self, is_listening):
        """Змінює іконку (біла/зелена)."""
        if self.icon_instance:
            new_icon = self.icon_listening if is_listening else self.icon_default
            # Оновлення іконки має відбуватися у головному потоці,
            # але pystray зазвичай сам з цим справляється
            self.icon_instance.icon = new_icon