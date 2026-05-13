# hotkey_manager.py
import asyncio
import threading
import keyboard
import config_manager as cfg
from logger_config import get_logger
import smart_ai
from audio_player import speak_text

logger = get_logger('hotkey_manager')

# Команда яка надсилається напряму до task_solver без wake word і STT
TASK_SOLVER_PROMPT = "проаналізуй і виріши завдання на екрані"

# Захист від повторного спрацювання поки виконується попередній запит
_task_solver_running = False
_lock = threading.Lock()

# Посилання на tray_manager — встановлюється з main.py через set_tray()
_tray = None


def set_tray(tray_manager):
    """Передає посилання на TrayManager для керування іконкою."""
    global _tray
    _tray = tray_manager


def _run_task_solver():
    """Запускає task_solver у окремому event loop (викликається з потоку hotkey)."""
    global _task_solver_running

    with _lock:
        if _task_solver_running:
            logger.info("task_solver вже виконується — ігнорую повторне натискання")
            return
        _task_solver_running = True

    try:
        logger.info("Hotkey: запускаю task_solver напряму")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(_execute_task_solver())
        finally:
            loop.close()

    except Exception as e:
        logger.error(f"Помилка hotkey task_solver: {e}")
    finally:
        with _lock:
            _task_solver_running = False


async def _execute_task_solver():
    """Async логіка: викликає task_solver напряму, ігноруючи disabledPlugins."""
    if not smart_ai.smart_assistant:
        logger.warning("ШІ асистент не ініціалізований — hotkey task_solver не може працювати")
        return

    try:
        config = cfg.load_config()
    except Exception:
        config = {}

    # Оранжева іконка — чекаємо відповідь від Gemini
    if _tray:
        _tray.set_icon_thinking(True)

    try:
        logger.info("task_solver hotkey: викликаю плагін напряму (минаю disabledPlugins)")

        from plugins.task_solver import TaskSolverPlugin
        plugin = TaskSolverPlugin()
        result = await plugin.execute_command("solve_task", value=TASK_SOLVER_PROMPT)

        if not result.get("success"):
            logger.error(f"task_solver повернув помилку: {result.get('message')}")
            return

        speak = result.get("speak_text")
        if speak:
            logger.info(f"task_solver hotkey TTS: '{speak[:80]}'")
            await asyncio.to_thread(speak_text, speak, config)

    except Exception as e:
        logger.error(f"Помилка виклику TaskSolverPlugin: {e}")
    finally:
        # Повертаємо стандартну іконку в будь-якому випадку
        if _tray:
            _tray.set_icon_thinking(False)


def _on_hotkey_triggered():
    """Callback від keyboard — запускає task_solver у фоновому потоці."""
    t = threading.Thread(target=_run_task_solver, daemon=True)
    t.start()


def start_hotkey_listener():
    """
    Реєструє глобальні хоткеї і запускає listener у фоновому потоці.
    PGUP → task_solver
    """
    try:
        keyboard.add_hotkey('left shift+left alt+up', _on_hotkey_triggered, suppress=False)
        logger.info("Hotkey зареєстровано: LShift+LAlt+Up → task_solver")

        # keyboard.wait() блокує потік — запускаємо в daemon потоці
        def _listener_thread():
            keyboard.wait()  # тримає listener живим

        t = threading.Thread(target=_listener_thread, daemon=True)
        t.start()
        logger.info("Hotkey listener запущено у фоновому потоці")

    except Exception as e:
        logger.error(f"Не вдалося зареєструвати hotkey: {e}")
