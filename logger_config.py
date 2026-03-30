# logger_config.py
import logging
import sys
import io
from datetime import datetime
from pathlib import Path


def _get_logs_dir() -> Path:
    """Повертає папку logs поруч з exe або скриптом."""
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).parent
    return base_dir / "logs"


def _get_timestamp() -> str:
    return datetime.now().strftime("[%d.%m.%y %H:%M:%S]")


def _rotate_logs(logs_dir: Path):
    """При старті переміщує поточні логи в backup якщо вони існують і не порожні."""
    files_to_rotate = ["main.txt", "errors.txt", "commands.txt", "commands_ai.txt"]

    # Визначаємо дату останнього запису (беремо з mtime будь-якого існуючого файлу)
    backup_date = None
    for fname in files_to_rotate:
        f = logs_dir / fname
        if f.exists() and f.stat().st_size > 0:
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            backup_date = mtime.strftime("%Y-%m-%d")
            break

    if backup_date is None:
        return  # Немає що ротувати

    # Не ротуємо якщо backup вже сьогодні (повторний запуск в той самий день)
    today = datetime.now().strftime("%Y-%m-%d")
    if backup_date == today:
        return

    backup_dir = logs_dir / f"backup_{backup_date}"
    backup_dir.mkdir(exist_ok=True)

    for fname in files_to_rotate:
        src = logs_dir / fname
        if src.exists() and src.stat().st_size > 0:
            dst = backup_dir / fname
            src.rename(dst)

    # Ротуємо папку plugins
    plugins_dir = logs_dir / "plugins"
    if plugins_dir.exists():
        backup_plugins = backup_dir / "plugins"
        backup_plugins.mkdir(exist_ok=True)
        for pf in plugins_dir.glob("*.txt"):
            if pf.stat().st_size > 0:
                pf.rename(backup_plugins / pf.name)


def setup_logger(name='alexa_assistant', level=logging.WARNING):
    """Налаштовує logging для асистента."""
    logs_dir = _get_logs_dir()
    logs_dir.mkdir(exist_ok=True)
    (logs_dir / "plugins").mkdir(exist_ok=True)

    _rotate_logs(logs_dir)

    # Формат для файлів
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s | %(filename)s:%(lineno)d',
        datefmt='%d.%m.%y %H:%M:%S'
    )

    # Консольний handler (тільки якщо є консоль — в exe з --noconsole sys.stdout == None)
    console_handler = None
    if sys.stdout is not None:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s | %(filename)s:%(lineno)d',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))

    # main.txt — INFO і вище (системні логи)
    main_handler = logging.FileHandler(logs_dir / "main.txt", encoding='utf-8')
    main_handler.setLevel(logging.INFO)
    main_handler.setFormatter(file_format)

    # errors.txt — WARNING і вище
    error_handler = logging.FileHandler(logs_dir / "errors.txt", encoding='utf-8')
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(file_format)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    if console_handler:
        logger.addHandler(console_handler)
    logger.addHandler(main_handler)
    logger.addHandler(error_handler)
    logger.propagate = False

    return logger


# Глобальний логер
logger = setup_logger()


def get_logger(module_name: str) -> logging.Logger:
    """Отримує логер для конкретного модуля."""
    return logging.getLogger(f'alexa_assistant.{module_name}')


def get_plugin_log_path(plugin_name: str) -> Path:
    """Повертає шлях до лог-файлу плагіна."""
    return _get_logs_dir() / "plugins" / f"{plugin_name}.txt"


class capture_plugin_output:
    """
    Async контекстний менеджер: перехоплює stdout під час виконання команди плагіна
    і записує все в logs/plugins/<plugin_name>.txt.
    Підтримує await всередині (asyncio.sleep тощо).
    """
    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        self.log_path = get_plugin_log_path(plugin_name)
        self.errors_path = _get_logs_dir() / "errors.txt"
        self.timestamp = _get_timestamp()
        self.separator = "=" * 48
        self.buffer = io.StringIO()
        self.old_stdout = None
        self.old_stderr = None

    def __enter__(self):
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr

        buffer = self.buffer
        old_stdout = self.old_stdout
        errors_path = self.errors_path
        plugin_name = self.plugin_name
        timestamp = self.timestamp

        class PluginStream:
            def write(self, text):
                buffer.write(text)
                if old_stdout is not None:
                    try:
                        old_stdout.write(text)
                    except Exception:
                        pass
            def flush(self):
                buffer.flush()
                if old_stdout is not None:
                    try:
                        old_stdout.flush()
                    except Exception:
                        pass

        class ErrorStream:
            def write(self, text):
                buffer.write(text)
                try:
                    if sys.__stderr__ is not None:
                        sys.__stderr__.write(text)
                except Exception:
                    pass
                if text.strip():
                    try:
                        with open(errors_path, 'a', encoding='utf-8') as f:
                            f.write(f"{timestamp} | PLUGIN:{plugin_name} | {text}")
                    except Exception:
                        pass
            def flush(self):
                buffer.flush()

        sys.stdout = PluginStream()
        sys.stderr = ErrorStream()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        self._flush_to_file()

    async def __aenter__(self):
        return self.__enter__()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        self._flush_to_file()

    def _flush_to_file(self):
        output = self.buffer.getvalue()
        if output.strip():
            try:
                with open(self.log_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n{self.separator}\n")
                    f.write(f"{self.timestamp}\n")
                    f.write(output)
                    if not output.endswith('\n'):
                        f.write('\n')
            except Exception as e:
                if self.old_stdout:
                    self.old_stdout.write(f"[logger] Не вдалося записати лог плагіна {self.plugin_name}: {e}\n")
