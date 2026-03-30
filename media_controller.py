import os
import asyncio
import psutil
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager


class MediaStateManager:
    """Керує станом аудіо при активації асистента."""

    def __init__(self):
        self.was_paused_by_assistant = False
        # Збережені гучності: {pid: (volume, session)}
        self._saved_volumes: dict = {}
        self._own_pid = os.getpid()

    # ─── Windows Media API (пауза відео/медіа) ────────────────────────────────

    async def _get_media_session(self):
        try:
            manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()
            return manager.get_current_session()
        except Exception as e:
            print(f"[MEDIA] Помилка отримання медіа-сесії: {e}")
            return None

    async def _pause_media_async(self):
        """Зупиняє медіа через Windows Media API."""
        self.was_paused_by_assistant = False
        session = await self._get_media_session()
        if session:
            info = session.get_playback_info()
            if info and info.playback_status == 4:  # 4 = Playing
                print("[MEDIA] Знайдено активне відтворення. Ставлю на паузу...")
                await session.try_pause_async()
                self.was_paused_by_assistant = True
                return True
        print("[MEDIA] Медіа не грає або вже на паузі. Залишаю як є.")
        return False

    async def _resume_media_async(self):
        """Відновлює медіа через Windows Media API."""
        if not self.was_paused_by_assistant:
            print("[MEDIA] Відновлення скасовано: асистент не зупиняв медіа.")
            return
        session = await self._get_media_session()
        if session:
            info = session.get_playback_info()
            if info and info.playback_status == 5:  # 5 = Paused
                print("[MEDIA] Відновлюю відтворення...")
                await session.try_play_async()
            else:
                print("[MEDIA] Відновлення не потрібне.")
        self.was_paused_by_assistant = False

    # ─── pycaw (мют усіх аудіо-сесій крім себе) ──────────────────────────────

    def _mute_all_except_self(self):
        """Зберігає поточні гучності і мютить всі сесії крім власного процесу."""
        self._saved_volumes.clear()
        try:
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                if not session or session.ProcessId == 0:
                    continue
                # Пропускаємо власний процес і всіх його нащадків
                try:
                    proc = psutil.Process(session.ProcessId)
                    # Перевіряємо чи це ми самі або наш нащадок
                    if session.ProcessId == self._own_pid:
                        continue
                    try:
                        if proc.ppid() == self._own_pid:
                            continue
                    except Exception:
                        pass
                except psutil.NoSuchProcess:
                    continue

                try:
                    vol_ctrl = session._ctl.QueryInterface(ISimpleAudioVolume)
                    current_vol = vol_ctrl.GetMasterVolume()
                    if current_vol > 0:
                        self._saved_volumes[session.ProcessId] = (current_vol, vol_ctrl)
                        # Discord — знижуємо до 30%, решта — до 7%
                        try:
                            proc_name = psutil.Process(session.ProcessId).name().lower()
                        except Exception:
                            proc_name = ""
                        target_vol = 0.30 if "discord" in proc_name else 0.07
                        vol_ctrl.SetMasterVolume(target_vol, None)
                except Exception:
                    continue

            if self._saved_volumes:
                names = []
                for pid in self._saved_volumes:
                    try:
                        names.append(psutil.Process(pid).name())
                    except Exception:
                        names.append(str(pid))
                print(f"[MEDIA] Мютую: {', '.join(names)}")
        except Exception as e:
            print(f"[MEDIA] Помилка мютування: {e}")

    def _restore_all_volumes(self):
        """Відновлює збережені гучності."""
        if not self._saved_volumes:
            return
        restored = []
        for pid, (vol, vol_ctrl) in self._saved_volumes.items():
            try:
                vol_ctrl.SetMasterVolume(vol, None)
                try:
                    restored.append(psutil.Process(pid).name())
                except Exception:
                    restored.append(str(pid))
            except Exception:
                continue
        if restored:
            print(f"[MEDIA] Відновлюю гучність: {', '.join(restored)}")
        self._saved_volumes.clear()

    # ─── Публічні синхронні методи ────────────────────────────────────────────

    def pause_if_playing(self):
        """Мютить всі аудіо-сесії крім себе + зупиняє медіа."""
        try:
            asyncio.run(self._pause_media_async())
        except Exception as e:
            print(f"[MEDIA] Помилка зупинки медіа: {e}")
        self._mute_all_except_self()

    def resume_if_paused(self):
        """Відновлює гучності + відновлює медіа."""
        self._restore_all_volumes()
        try:
            asyncio.run(self._resume_media_async())
        except Exception as e:
            print(f"[MEDIA] Помилка відновлення медіа: {e}")


# Один екземпляр для всього проєкту
media_manager = MediaStateManager()
