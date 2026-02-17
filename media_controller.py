# media_controller.py
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
import keyboard
import time

class MediaStateManager:
    """Керує станом аудіо-сесій, щоб розумно ставити на паузу."""

    def __init__(self):
        # Тут ми будемо зберігати процеси, які ми поставили на паузу
        self.paused_by_assistant = set()

    def _is_session_audible(self, session):
        """Перевіряє, чи сесія зараз відтворює звук."""
        try:
            # Перевіряємо, чи сесія не зам'ючена і має гучність > 0
            volume = session.SimpleAudioVolume
            if volume.GetMute() == 1 or volume.GetMasterVolume() == 0:
                return False
            
            # session.State == 1 означає, що сесія активна (відтворює звук)
            if session.State == 1:
                return True
        except Exception:
            # Якщо сесія закрилася під час перевірки, ігноруємо
            return False
        return False

    def pause_if_playing(self):
        """
        Знаходить активні аудіо-сесії. Якщо вони відтворюють звук,
        надсилає сигнал Play/Pause і запам'ятовує процеси.
        Не робить нічого якщо музика вже на паузі.
        """
        self.paused_by_assistant.clear() # Очищуємо перед новою операцією

        found_playing_session = False
        try:
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                if session.Process and self._is_session_audible(session):
                    # Запам'ятовуємо ім'я процесу тільки якщо він реально відтворює
                    self.paused_by_assistant.add(session.Process.name())
                    found_playing_session = True

            if found_playing_session:
                print("[MEDIA] Знайдено активне відтворення. Ставлю на паузу...")
                keyboard.press_and_release('play/pause')
                return True  # Повертаємо True якщо щось поставили на паузу
            else:
                print("[MEDIA] Активного відтворення не знайдено. Залишаю як є.")
                return False  # Повертаємо False якщо нічого не змінили

        except Exception as e:
            print(f"Помилка при спробі поставити медіа на паузу: {e}")
            return False

    def resume_if_paused(self):
        """
        Якщо асистент раніше ставив щось на паузу,
        надсилає сигнал Play/Pause для відновлення.
        """
        if not self.paused_by_assistant:
            print("[MEDIA] Нема процесів для відновлення.")
            return

        print("[MEDIA] Відновлення відтворення для раніше зупинених процесів...")
        try:
            # Перевіряємо, чи хоча б один із зупинених процесів все ще активний
            should_resume = False
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                if session.Process and session.Process.name() in self.paused_by_assistant:
                    should_resume = True
                    break

            if should_resume:
                keyboard.press_and_release('play/pause')
                print("[MEDIA] Відновлено відтворення.")
            else:
                print("[MEDIA] Раніше зупинені процеси більше не активні.")

        except Exception as e:
            print(f"Помилка при спробі відновити медіа: {e}")
        finally:
            self.paused_by_assistant.clear() # Очищуємо список у будь-якому випадку

# Створюємо один екземпляр для всього проєкту
media_manager = MediaStateManager()