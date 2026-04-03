# speed_logger.py
"""
Логує детальний timeline кожної сесії від wake word до кінця TTS.
Записує в logs/speed.txt — кожна сесія окремим блоком.
"""
import time
from datetime import datetime
from pathlib import Path
import sys


def _get_logs_dir() -> Path:
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).parent
    return base_dir / "logs"


SEP = "=" * 56


class SessionTimer:
    """Timeline одної сесії (від wake word до кінця TTS)."""

    def __init__(self, mode: str = "google_stt"):
        """
        mode: 'google_stt' або 'gemini_audio'
        """
        self.mode = mode
        self.t0 = time.perf_counter()  # абсолютна точка відліку
        self.events: list[tuple[str, float]] = []  # (label, elapsed)
        self._mark("Wake word")

    def _elapsed(self) -> float:
        return time.perf_counter() - self.t0

    def _mark(self, label: str):
        self.events.append((label, self._elapsed()))

    # ── публічні хуки ──────────────────────────────────────────

    def on_listen_start(self):
        self._mark("Початок слухання мікрофона")

    def on_speech_start(self):
        self._mark("Користувач почав говорити")

    def on_speech_end(self):
        self._mark("Користувач перестав говорити")

    def on_audio_ready(self, size_bytes: int = 0):
        label = f"Аудіо захоплено ({size_bytes / 1024:.1f} KB / {size_bytes / 1024 / 1024:.2f} MB)"
        self._mark(label)

    def on_stt_start(self):
        """Google STT — відправили запит"""
        self._mark("Відправили Google STT")

    def on_stt_done(self, transcript: str = ""):
        label = f"Google STT відповів: '{transcript[:60]}'" if transcript else "Google STT: тиша/помилка"
        self._mark(label)

    def on_gemini_start(self):
        self._mark("Відправили Gemini")

    def on_gemini_done(self, function_calls: int = 0):
        self._mark(f"Gemini відповів ({function_calls} function call(s))")

    def on_plugin_start(self, plugin: str, command: str):
        self._mark(f"Плагін старт: {plugin}.{command}")

    def on_plugin_done(self, plugin: str, command: str, success: bool):
        status = "OK" if success else "FAIL"
        self._mark(f"Плагін завершено: {plugin}.{command} [{status}]")

    def on_tts_start(self, text: str = ""):
        label = f"TTS старт: '{text[:50]}'" if text else "TTS старт"
        self._mark(label)

    def on_tts_done(self):
        self._mark("TTS завершено")

    def on_session_end(self):
        self._mark("Сесія завершена")

    # ── запис у файл ───────────────────────────────────────────

    def save(self):
        """Зберігає timeline в logs/speed.txt (append)."""
        logs_dir = _get_logs_dir()
        logs_dir.mkdir(exist_ok=True)
        path = logs_dir / "speed.txt"

        ts = datetime.now().strftime("[%d.%m.%y %H:%M:%S]")
        lines = [f"\n{SEP}", f"{ts}  [{self.mode.upper()}]"]

        prev = 0.0
        for label, elapsed in self.events:
            delta = elapsed - prev
            lines.append(f"  {elapsed:8.4f}s  (+{delta:.4f}s)  {label}")
            prev = elapsed

        total = self.events[-1][1] if self.events else 0
        lines.append(f"  {'─'*48}")
        lines.append(f"  ВСЬОГО: {total:.4f}s")
        lines.append(f"{SEP}\n")

        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
        except Exception as e:
            print(f"[SpeedLogger] Помилка запису: {e}")


# Глобальний таймер поточної сесії (None між сесіями)
current_session: SessionTimer | None = None


def start_session(mode: str = "google_stt") -> SessionTimer:
    global current_session
    current_session = SessionTimer(mode)
    return current_session


def get_session() -> SessionTimer | None:
    return current_session


def end_session():
    global current_session
    if current_session:
        current_session.on_session_end()
        current_session.save()
        current_session = None
