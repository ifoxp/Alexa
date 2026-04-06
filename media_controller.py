import os
import json
import asyncio
import threading
import psutil
from pycaw.pycaw import AudioUtilities, ISimpleAudioVolume
from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager

# Гучності під час duck (програмні, не користувацькі)
DUCK_VOL_DEFAULT = 0.07
DUCK_VOL_DISCORD = 0.32

# Файл зі збереженими оригінальними гучностями
_STATE_FILE = "audio_state.json"

def _get_state_path() -> str:
    """Шлях до audio_state.json поряд з виконуваним файлом або скриптом."""
    base = getattr(__import__('sys'), 'frozen', False) and os.path.dirname(__import__('sys').executable) or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, _STATE_FILE)


def _load_state() -> dict:
    """Завантажує збережені оригінальні гучності з файлу."""
    path = _get_state_path()
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_state(state: dict):
    """Зберігає оригінальні гучності у файл."""
    path = _get_state_path()
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[MEDIA] Помилка збереження стану: {e}")


def _clear_state():
    """Очищає файл стану після успішного відновлення."""
    path = _get_state_path()
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


class MediaStateManager:
    """Керує станом аудіо при активації асистента."""

    def __init__(self):
        self.was_paused_by_assistant = False
        # Збережені гучності в пам'яті: {pid: (volume, vol_ctrl)}
        self._saved_volumes: dict = {}
        self._own_pid = os.getpid()
        # Watchdog
        self._watchdog_thread: threading.Thread | None = None
        self._watchdog_stop = threading.Event()

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

    # ─── pycaw (duck/restore гучності) ──────────────────────────────────────

    def _mute_all_except_self(self):
        """Зберігає поточні гучності (в пам'ять + файл) і знижує всі сесії крім себе."""
        self._saved_volumes.clear()
        file_state: dict = {}

        try:
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                if not session or session.ProcessId == 0:
                    continue
                try:
                    proc = psutil.Process(session.ProcessId)
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
                        try:
                            proc_name = psutil.Process(session.ProcessId).name().lower()
                        except Exception:
                            proc_name = ""

                        # Зберігаємо лише якщо це не вже задакована гучність
                        is_duck_vol = abs(current_vol - DUCK_VOL_DISCORD) < 0.01 or abs(current_vol - DUCK_VOL_DEFAULT) < 0.01
                        if not is_duck_vol:
                            self._saved_volumes[session.ProcessId] = (current_vol, vol_ctrl)
                            file_state[str(session.ProcessId)] = {
                                "name": proc_name,
                                "volume": current_vol,
                            }

                        target_vol = DUCK_VOL_DISCORD if "discord" in proc_name else DUCK_VOL_DEFAULT
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
                _save_state(file_state)

        except Exception as e:
            print(f"[MEDIA] Помилка мютування: {e}")

    def _restore_all_volumes(self):
        """Відновлює збережені гучності з пам'яті."""
        if not self._saved_volumes:
            # Спробуємо з файлу (на випадок краш-відновлення)
            self._restore_from_file()
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
        _clear_state()

    def _restore_from_file(self):
        """Відновлює гучності з файлу (watchdog або краш-відновлення)."""
        state = _load_state()
        if not state:
            return

        restored = []
        try:
            sessions = AudioUtilities.GetAllSessions()
            session_map = {}
            for session in sessions:
                if session and session.ProcessId != 0:
                    session_map[session.ProcessId] = session

            for pid_str, info in state.items():
                try:
                    pid = int(pid_str)
                    target_vol = info.get("volume", 1.0)
                    proc_name = info.get("name", "")

                    if pid in session_map:
                        vol_ctrl = session_map[pid]._ctl.QueryInterface(ISimpleAudioVolume)
                        vol_ctrl.SetMasterVolume(target_vol, None)
                        restored.append(proc_name or str(pid))
                    else:
                        # Процес може мати новий PID — шукаємо по назві
                        for session in sessions:
                            if not session or session.ProcessId == 0:
                                continue
                            try:
                                name = psutil.Process(session.ProcessId).name().lower()
                                if name == proc_name.lower():
                                    vol_ctrl = session._ctl.QueryInterface(ISimpleAudioVolume)
                                    vol_ctrl.SetMasterVolume(target_vol, None)
                                    restored.append(proc_name)
                                    break
                            except Exception:
                                continue
                except Exception:
                    continue
        except Exception as e:
            print(f"[MEDIA] Помилка відновлення з файлу: {e}")

        if restored:
            print(f"[MEDIA] Watchdog відновив гучність: {', '.join(restored)}")
        _clear_state()

    # ─── Watchdog ─────────────────────────────────────────────────────────────

    def _watchdog_loop(self):
        """Раз на хвилину перевіряє чи не застрягли програми на duck-гучності."""
        while not self._watchdog_stop.wait(60):
            state = _load_state()
            if not state:
                continue  # Нічого не збережено — все добре

            # Перевіряємо чи є хоч один процес що застряг на duck-рівні
            found_stuck = False
            try:
                sessions = AudioUtilities.GetAllSessions()
                for session in sessions:
                    if not session or session.ProcessId == 0:
                        continue
                    pid_str = str(session.ProcessId)
                    if pid_str not in state:
                        # Шукаємо по назві
                        try:
                            name = psutil.Process(session.ProcessId).name().lower()
                            for saved_pid, info in state.items():
                                if info.get("name", "").lower() == name:
                                    pid_str = saved_pid
                                    break
                            else:
                                continue
                        except Exception:
                            continue
                    try:
                        vol_ctrl = session._ctl.QueryInterface(ISimpleAudioVolume)
                        current = vol_ctrl.GetMasterVolume()
                        is_stuck = abs(current - DUCK_VOL_DEFAULT) < 0.01 or abs(current - DUCK_VOL_DISCORD) < 0.01
                        if is_stuck:
                            found_stuck = True
                            break
                    except Exception:
                        continue
            except Exception:
                continue

            if found_stuck:
                print("[MEDIA] Watchdog: знайдено застряглу гучність, відновлюю...")
                self._restore_from_file()

    def start_watchdog(self):
        """Запускає фоновий watchdog-потік."""
        if self._watchdog_thread and self._watchdog_thread.is_alive():
            return
        self._watchdog_stop.clear()
        self._watchdog_thread = threading.Thread(
            target=self._watchdog_loop,
            name="AudioWatchdog",
            daemon=True,
        )
        self._watchdog_thread.start()
        print("[MEDIA] Watchdog запущено.")

    def stop_watchdog(self):
        """Зупиняє watchdog."""
        self._watchdog_stop.set()

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
