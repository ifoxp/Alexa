# smart_plugin_manager.py
import os
import sys
import asyncio
import importlib.util
import inspect
from typing import Dict, List, Any, Optional
from plugins.base_plugin import SmartPlugin
from logger_config import get_logger

logger = get_logger('smart_plugin_manager')


def _find_python_executable() -> str:
    """Знаходить системний python.exe (не Alexa.exe)."""
    import shutil
    # В exe-режимі sys.executable = Alexa.exe, шукаємо справжній python
    if hasattr(sys, '_MEIPASS'):
        python = shutil.which('python') or shutil.which('python3')
        if python:
            return python
        # Шукаємо поруч з _MEIPASS (python311.dll є в _internal — там же python.exe не буде,
        # але можна знайти через реєстр або стандартні шляхи)
        for candidate in [
            r'C:\Users\{}\AppData\Local\Programs\Python\Python311\python.exe'.format(os.environ.get('USERNAME', '')),
            r'C:\Python311\python.exe', r'C:\Python310\python.exe',
        ]:
            if os.path.exists(candidate):
                return candidate
        return 'python'  # fallback
    return sys.executable


def _pip_install(package: str) -> bool:
    """Встановлює пакет через pip і повертає True якщо успішно."""
    try:
        import subprocess
        # Деякі модулі мають іншу назву пакета для pip
        PIP_ALIASES = {
            'win32gui': 'pywin32',
            'win32api': 'pywin32',
            'win32con': 'pywin32',
            'pywintypes': 'pywin32',
        }
        pip_package = PIP_ALIASES.get(package, package)
        python = _find_python_executable()
        logger.info(f"Auto-installing missing package: {pip_package} via {python}")
        result = subprocess.run(
            [python, '-m', 'pip', 'install', pip_package, '--quiet'],
            capture_output=True, text=True, timeout=60,
            creationflags=0x08000000 if os.name == 'nt' else 0  # CREATE_NO_WINDOW
        )
        if result.returncode == 0:
            logger.info(f"Successfully installed: {package}")
            # pywin32 потребує post-install для реєстрації DLL
            if pip_package == 'pywin32':
                try:
                    r = subprocess.run([python, '-c',
                        'import sysconfig; print(sysconfig.get_path("scripts"))'],
                        capture_output=True, text=True, timeout=5,
                        creationflags=0x08000000 if os.name == 'nt' else 0)
                    if r.returncode == 0:
                        post_install = os.path.join(r.stdout.strip(), 'pywin32_postinstall.py')
                        if os.path.exists(post_install):
                            subprocess.run([python, post_install, '-install'],
                                capture_output=True, text=True, timeout=30,
                                creationflags=0x08000000 if os.name == 'nt' else 0)
                            logger.info("pywin32 post-install completed")
                except Exception as pe:
                    logger.warning(f"pywin32 post-install failed: {pe}")
            return True
        else:
            logger.error(f"pip install {package} failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"pip install {package} error: {e}")
        return False


def _add_user_site_packages():
    """Додає site-packages системного Python до sys.path (де pip встановлює пакети)."""
    try:
        import subprocess
        python = _find_python_executable()
        result = subprocess.run(
            [python, '-c', 'import site, json; print(json.dumps(site.getsitepackages() + [site.getusersitepackages()]))'],
            capture_output=True, text=True, timeout=10,
            creationflags=0x08000000 if os.name == 'nt' else 0  # CREATE_NO_WINDOW
        )
        if result.returncode == 0:
            import json
            for path in json.loads(result.stdout.strip()):
                if os.path.exists(path) and path not in sys.path:
                    sys.path.insert(0, path)
    except Exception:
        pass


def _extract_missing_module(error_msg: str) -> str | None:
    """Витягує назву відсутнього модуля з повідомлення ImportError."""
    import re
    m = re.search(r"No module named '([^']+)'", error_msg)
    if m:
        # Беремо тільки верхньорівневий пакет (screen_brightness_control, не sub.module)
        return m.group(1).split('.')[0]
    return None


def _load_plugin_file(plugins_dir: str, filename: str) -> List[type]:
    """Завантажує один файл плагіна, при потребі встановлює залежності."""
    plugin_path = os.path.join(plugins_dir, filename)
    full_module_name = f'plugins.{filename[:-3]}'

    for attempt in range(2):
        try:
            # Очищаємо кеш модуля перед повторною спробою
            if full_module_name in sys.modules:
                del sys.modules[full_module_name]

            spec = importlib.util.spec_from_file_location(
                full_module_name, plugin_path, submodule_search_locations=[])
            if spec is None or spec.loader is None:
                return []

            module = importlib.util.module_from_spec(spec)
            module.__package__ = 'plugins'
            sys.modules[full_module_name] = module
            spec.loader.exec_module(module)

            classes = []
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj != SmartPlugin and issubclass(obj, SmartPlugin):
                    classes.append(obj)
            return classes

        except ImportError as e:
            if attempt == 0:
                missing = _extract_missing_module(str(e))
                if missing:
                    _add_user_site_packages()
                    installed = _pip_install(missing)
                    _add_user_site_packages()
                    logger.info(f"sys.path after install: {[p for p in sys.path if 'site-packages' in p]}")
                    if installed:
                        continue  # друга спроба
            logger.error(f"Failed to load plugin file {filename}: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to load plugin file {filename}: {e}")
            return []

    return []


def discover_plugins() -> List[type]:
    """Автоматично знаходить всі плагіни в папці plugins/ (для exe-режиму)."""
    plugin_classes = []

    # Папка з .py файлами плагінів (поруч з exe)
    plugins_dir = os.path.join(os.path.dirname(sys.executable), 'plugins')
    if not os.path.exists(plugins_dir):
        logger.error(f"plugins/ not found at: {plugins_dir}")
        return plugin_classes

    # Додаємо _internal/ до sys.path — там PyInstaller пакує вбудовані залежності
    exe_dir = os.path.dirname(sys.executable)
    internal_dir = os.path.join(exe_dir, '_internal')
    for d in [exe_dir, internal_dir]:
        if os.path.exists(d) and d not in sys.path:
            sys.path.insert(0, d)

    # Також додаємо системні site-packages одразу
    _add_user_site_packages()

    # Реєструємо пакет plugins у sys.modules щоб працював from .base_plugin import ...
    if 'plugins' not in sys.modules:
        import types
        plugins_pkg = types.ModuleType('plugins')
        plugins_pkg.__path__ = [plugins_dir]
        plugins_pkg.__package__ = 'plugins'
        sys.modules['plugins'] = plugins_pkg

    # Завантажуємо base_plugin першим
    base_plugin_path = os.path.join(plugins_dir, 'base_plugin.py')
    if os.path.exists(base_plugin_path) and 'plugins.base_plugin' not in sys.modules:
        spec = importlib.util.spec_from_file_location('plugins.base_plugin', base_plugin_path,
            submodule_search_locations=[])
        base_module = importlib.util.module_from_spec(spec)
        base_module.__package__ = 'plugins'
        sys.modules['plugins.base_plugin'] = base_module
        spec.loader.exec_module(base_module)

    # Сканування всіх .py файлів
    for filename in sorted(os.listdir(plugins_dir)):
        if filename.endswith('.py') and not filename.startswith('_') and filename != 'base_plugin.py':
            plugin_classes.extend(_load_plugin_file(plugins_dir, filename))

    return plugin_classes


def _load_disabled_plugins() -> set:
    """Читає список вимкнених плагінів з config.json."""
    import json
    try:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
        if not os.path.exists(config_path):
            # exe-режим: шукаємо config.json поруч з exe
            config_path = os.path.join(os.path.dirname(sys.executable), 'config.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            disabled = data.get('disabledPlugins', [])
            if disabled:
                logger.info(f"Disabled plugins from config: {disabled}")
            return set(disabled)
    except Exception as e:
        logger.warning(f"Could not read disabledPlugins from config: {e}")
    return set()


class SmartPluginManager:
    """Менеджер розумних плагінів для GPT-інтеграції."""

    def __init__(self):
        self.plugins: Dict[str, SmartPlugin] = {}
        self.load_plugins()

    def load_plugins(self):
        """Завантажує всі доступні плагіни (крім вимкнених у config.json)."""
        disabled_plugins = _load_disabled_plugins()

        if hasattr(sys, '_MEIPASS'):
            # В exe-режимі плагіни як .py файли поруч з exe — завантажуємо динамічно
            available_plugins = discover_plugins()
        else:
            try:
                from plugins import AVAILABLE_PLUGINS
                available_plugins = AVAILABLE_PLUGINS
            except ImportError:
                available_plugins = discover_plugins()


        for plugin_class in available_plugins:
            try:
                plugin_instance = plugin_class()

                # Перевіряємо чи instance має необхідні атрибути
                if not hasattr(plugin_instance, 'name'):
                    logger.error(f"Plugin instance {plugin_class.__name__} has no 'name' property")
                    continue

                if not hasattr(plugin_instance, 'description'):
                    logger.error(f"Plugin instance {plugin_class.__name__} has no 'description' property")
                    continue

                plugin_name = plugin_instance.name
                plugin_description = plugin_instance.description

                if plugin_name in disabled_plugins:
                    logger.info(f"Skipping disabled plugin: {plugin_name}")
                    continue

                self.plugins[plugin_name] = plugin_instance

            except Exception as e:
                import traceback
                logger.error(f"Failed to load plugin {plugin_class.__name__}", extra={
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'traceback': traceback.format_exc()
                })


    def get_plugins_summary(self) -> List[Dict[str, Any]]:
        """
        Повертає короткий список плагінів для GPT (етап 1).

        Returns:
            List з short info про кожен плагін
        """
        plugins_summary = []


        for plugin_name, plugin in self.plugins.items():
            try:
                if plugin is None:
                    logger.error(f"Plugin {plugin_name} is None")
                    continue

                if not hasattr(plugin, 'name') or not hasattr(plugin, 'description'):
                    logger.error(f"Plugin {plugin_name} missing required attributes")
                    continue

                summary = {
                    "name": plugin.name,
                    "description": plugin.description
                }
                plugins_summary.append(summary)

            except Exception as e:
                logger.error(f"Error getting summary for plugin {plugin_name}", extra={'error': str(e)})
        return plugins_summary

    def get_plugin_commands(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """
        Повертає детальну інформацію про команди плагіна (етап 2).

        Args:
            plugin_name: назва плагіна

        Returns:
            Інформація про плагін та його команди або None
        """
        if plugin_name not in self.plugins:
            return None

        plugin = self.plugins[plugin_name]
        return {
            "name": plugin.name,
            "description": plugin.description,
            "commands": plugin.commands
        }

    async def execute_plugin_command(self, plugin_name: str, command_name: str, **kwargs) -> Dict[str, Any]:
        """
        Виконує команду плагіна.

        Args:
            plugin_name: назва плагіна
            command_name: назва команди
            **kwargs: параметри команди

        Returns:
            Результат виконання команди
        """
        if plugin_name not in self.plugins:
            return {
                "success": False,
                "result": None,
                "message": f"Плагін не знайдено: {plugin_name}"
            }

        plugin = self.plugins[plugin_name]

        try:
            from logger_config import capture_plugin_output
            async with asyncio.timeout(30):
                async with capture_plugin_output(plugin_name):
                    result = await plugin.execute_command(command_name, **kwargs)
            return result

        except Exception as e:
            logger.error(f"Error executing {plugin_name}.{command_name}", extra={'error': str(e)})
            return {
                "success": False,
                "result": None,
                "message": f"Помилка виконання команди: {str(e)}"
            }

    def get_plugin_by_name(self, plugin_name: str) -> Optional[SmartPlugin]:
        """Повертає плагін за назвою."""
        return self.plugins.get(plugin_name)

    def list_all_plugins(self) -> List[str]:
        """Повертає список назв всіх завантажених плагінів."""
        return list(self.plugins.keys())

    def get_plugins_count(self) -> int:
        """Повертає кількість завантажених плагінів."""
        return len(self.plugins)