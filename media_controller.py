import asyncio
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager

class MediaStateManager:
    """Керує станом аудіо-сесій за допомогою сучасного Windows Media API."""

    def __init__(self):
        # Прапорець, який показує, чи ми особисто зупинили музику
        self.was_paused_by_assistant = False

    async def _get_media_session(self):
        """Отримує поточну активну медіа-сесію (Spotify, YouTube, браузер тощо)"""
        try:
            manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()
            return manager.get_current_session()
        except Exception as e:
            print(f"[MEDIA] Помилка отримання медіа-сесії: {e}")
            return None

    async def _pause_async(self):
        """Асинхронна логіка точної паузи."""
        self.was_paused_by_assistant = False
        session = await self._get_media_session()
        
        if session:
            info = session.get_playback_info()
            # 4 означає Playing (грає), 5 означає Paused (на паузі)
            if info and info.playback_status == 4:
                print("[MEDIA] Знайдено активне відтворення. Ставлю чітко на паузу...")
                # Відправляємо конкретно сигнал ПАУЗИ, а не перемикач
                await session.try_pause_async()
                self.was_paused_by_assistant = True
                return True
                
        print("[MEDIA] Музика не грає (або вже на паузі). Залишаю як є.")
        return False

    async def _resume_async(self):
        """Асинхронна логіка точного відновлення відтворення."""
        if not self.was_paused_by_assistant:
            print("[MEDIA] Відновлення скасовано: асистент не зупиняв музику.")
            return

        session = await self._get_media_session()
        if session:
            info = session.get_playback_info()
            # 5 означає Paused
            if info and info.playback_status == 5:
                print("[MEDIA] Відновлюю відтворення музики...")
                # Відправляємо конкретно сигнал PLAY
                await session.try_play_async()
            else:
                print("[MEDIA] Відновлення не потрібне (музика вже грає або плеєр закрито).")
        
        # Скидаємо прапорець
        self.was_paused_by_assistant = False

    def pause_if_playing(self):
        """
        Синхронна обгортка. 
        Використовується у wake_word.py для зупинки музики.
        """
        try:
            # Запускаємо асинхронний код у синхронному середовищі
            return asyncio.run(self._pause_async())
        except Exception as e:
            print(f"[MEDIA] Помилка при спробі поставити медіа на паузу: {e}")
            return False

    def resume_if_paused(self):
        """
        Синхронна обгортка.
        Використовується у wake_word.py для відновлення музики.
        """
        try:
            asyncio.run(self._resume_async())
        except Exception as e:
            print(f"[MEDIA] Помилка при спробі відновити медіа: {e}")

# Створюємо один екземпляр для всього проєкту
media_manager = MediaStateManager()