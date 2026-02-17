# plugin_system.py
import os
import importlib
import importlib.util
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from logger_config import get_logger

logger = get_logger('plugin_system')


class CommandPlugin(ABC):
    """Базовий клас для всіх command плагінів."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Унікальне ім'я плагіна."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Опис функціоналу плагіна."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Версія плагіна."""
        pass

    @abstractmethod
    def can_handle(self, text: str, context: Dict[str, Any] = None) -> bool:
        """
        Перевіряє чи може цей плагін обробити команду.

        Args:
            text: Розпізнаний текст команди
            context: Додатковий контекст (мова, попередні команди, тощо)

        Returns:
            True якщо плагін може обробити команду
        """
        pass

    @abstractmethod
    def execute(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Виконує команду.

        Args:
            text: Розпізнаний текст команди
            context: Додатковий контекст

        Returns:
            Результат виконання команди з полями:
            - success: bool
            - message: str
            - data: Any (опціонально)
        """
        pass

    def get_example_commands(self) -> List[str]:
        """Повертає список прикладів команд які може обробити плагін."""
        return []

    def initialize(self) -> bool:
        """Ініціалізація плагіна. Викликається при завантаженні."""
        return True

    def cleanup(self):
        """Очищення ресурсів плагіна. Викликається при завершенні."""
        pass


class PluginManager:
    """Менеджер для завантаження та керування плагінами."""

    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = plugins_dir
        self.plugins: List[CommandPlugin] = []
        self.plugin_registry: Dict[str, CommandPlugin] = {}

    def load_plugins(self):
        """Завантажує всі плагіни з папки plugins."""
        logger.info("Starting plugin loading", extra={'plugins_dir': self.plugins_dir})

        if not os.path.exists(self.plugins_dir):
            logger.warning("Plugins directory not found", extra={'path': self.plugins_dir})
            os.makedirs(self.plugins_dir, exist_ok=True)
            return

        # Завантажуємо вбудовані плагіни
        self._load_builtin_plugins()

        # Завантажуємо зовнішні плагіни
        self._load_external_plugins()

        logger.info("Plugin loading completed", extra={
            'total_plugins': len(self.plugins),
            'plugin_names': [p.name for p in self.plugins]
        })

    def _load_builtin_plugins(self):
        """Завантажує вбудовані плагіни."""
        builtin_plugins = [
            WebsitePlugin(),
            ApplicationPlugin(),
            SystemVolumePlugin(),
            AppVolumePlugin(),
            ScriptPlugin()
        ]

        for plugin in builtin_plugins:
            if self._register_plugin(plugin):
                logger.info("Builtin plugin loaded", extra={
                    'plugin_name': plugin.name,
                    'plugin_version': plugin.version
                })

    def _load_external_plugins(self):
        """Завантажує зовнішні плагіни з файлів."""
        for filename in os.listdir(self.plugins_dir):
            if filename.endswith('_plugin.py') and not filename.startswith('__'):
                plugin_path = os.path.join(self.plugins_dir, filename)
                self._load_plugin_from_file(plugin_path)

    def _load_plugin_from_file(self, filepath: str):
        """Завантажує плагін з файлу."""
        try:
            module_name = os.path.splitext(os.path.basename(filepath))[0]
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Шукаємо клас що наслідує CommandPlugin
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, CommandPlugin) and
                    attr != CommandPlugin):

                    plugin = attr()
                    if self._register_plugin(plugin):
                        logger.info("External plugin loaded", extra={
                            'plugin_name': plugin.name,
                            'filepath': filepath,
                            'plugin_version': plugin.version
                        })

        except Exception as e:
            logger.error("Failed to load plugin", extra={
                'filepath': filepath,
                'error': str(e),
                'error_type': type(e).__name__
            })

    def _register_plugin(self, plugin: CommandPlugin) -> bool:
        """Реєструє плагін в системі."""
        try:
            if plugin.name in self.plugin_registry:
                logger.warning("Plugin name conflict", extra={
                    'plugin_name': plugin.name,
                    'action': 'skipping'
                })
                return False

            if plugin.initialize():
                self.plugins.append(plugin)
                self.plugin_registry[plugin.name] = plugin
                return True
            else:
                logger.warning("Plugin initialization failed", extra={'plugin_name': plugin.name})
                return False

        except Exception as e:
            logger.error("Plugin registration failed", extra={
                'plugin_name': getattr(plugin, 'name', 'unknown'),
                'error': str(e)
            })
            return False

    def find_handler(self, text: str, context: Dict[str, Any] = None) -> Optional[CommandPlugin]:
        """Знаходить плагін який може обробити команду."""
        context = context or {}

        # Додаємо пріоритет - перевіряємо плагіни в порядку реєстрації
        for plugin in self.plugins:
            try:
                if plugin.can_handle(text, context):
                    logger.debug("Plugin matched command", extra={
                        'plugin': plugin.name,
                        'text': text
                    })
                    return plugin
            except Exception as e:
                logger.error("Plugin matching error", extra={
                    'plugin': plugin.name,
                    'error': str(e)
                })

        logger.debug("No plugin found for command", extra={'text': text})
        return None

    def execute_command(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Виконує команду через відповідний плагін."""
        plugin = self.find_handler(text, context)

        if not plugin:
            return {
                'success': False,
                'message': f'Команду не знайдено: {text}',
                'plugin': None
            }

        try:
            result = plugin.execute(text, context)
            result['plugin'] = plugin.name

            logger.info("Command executed", extra={
                'plugin': plugin.name,
                'text': text,
                'success': result.get('success', False)
            })

            return result

        except Exception as e:
            error_result = {
                'success': False,
                'message': f'Помилка виконання команди: {str(e)}',
                'plugin': plugin.name
            }

            logger.error("Command execution error", extra={
                'plugin': plugin.name,
                'text': text,
                'error': str(e),
                'error_type': type(e).__name__
            })

            return error_result

    def get_all_plugins(self) -> List[CommandPlugin]:
        """Повертає список всіх завантажених плагінів."""
        return self.plugins.copy()

    def get_plugin_by_name(self, name: str) -> Optional[CommandPlugin]:
        """Повертає плагін за іменем."""
        return self.plugin_registry.get(name)

    def unload_all_plugins(self):
        """Вивантажує всі плагіни."""
        logger.info("Unloading all plugins")

        for plugin in self.plugins:
            try:
                plugin.cleanup()
            except Exception as e:
                logger.error("Plugin cleanup error", extra={
                    'plugin': plugin.name,
                    'error': str(e)
                })

        self.plugins.clear()
        self.plugin_registry.clear()

    def reload_plugins(self):
        """Перезавантажує всі плагіни."""
        logger.info("Reloading plugins")
        self.unload_all_plugins()
        self.load_plugins()


# Вбудовані плагіни (переписані з існуючого коду)

class WebsitePlugin(CommandPlugin):
    @property
    def name(self) -> str:
        return "website"

    @property
    def description(self) -> str:
        return "Відкриває веб-сайти та виконує пошук"

    @property
    def version(self) -> str:
        return "1.0.0"

    def can_handle(self, text: str, context: Dict[str, Any] = None) -> bool:
        text_lower = text.lower()
        keywords = ['відкрий', 'знайди', 'пошукай', 'гугл', 'youtube', 'google']
        return any(keyword in text_lower for keyword in keywords)

    def execute(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        import webbrowser

        text_lower = text.lower()

        # Визначаємо сайт та пошуковий запит
        if 'youtube' in text_lower or 'ютуб' in text_lower:
            url = "https://youtube.com/results?search_query="
            query = self._extract_search_query(text)
        elif 'google' in text_lower or 'гугл' in text_lower:
            url = "https://google.com/search?q="
            query = self._extract_search_query(text)
        else:
            # Загальний пошук в Google
            url = "https://google.com/search?q="
            query = text

        try:
            if query:
                full_url = url + "+".join(query.split())
                webbrowser.open(full_url)
                message = f"Відкриваю пошук: {query}"
            else:
                # Просто відкриваємо сайт
                site_url = "https://google.com"
                if 'youtube' in text_lower:
                    site_url = "https://youtube.com"

                webbrowser.open(site_url)
                message = f"Відкриваю сайт: {site_url}"

            return {
                'success': True,
                'message': message,
                'data': {'url': full_url if query else site_url}
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Помилка відкриття браузера: {str(e)}'
            }

    def _extract_search_query(self, text: str) -> str:
        """Витягує пошуковий запит з тексту."""
        # Видаляємо ключові слова команд
        keywords_to_remove = ['відкрий', 'знайди', 'пошукай', 'гугл', 'youtube', 'ютуб', 'google', 'в', 'на']

        words = text.lower().split()
        filtered_words = [word for word in words if word not in keywords_to_remove]

        return ' '.join(filtered_words).strip()

    def get_example_commands(self) -> List[str]:
        return [
            "знайди котиків на YouTube",
            "відкрий Google",
            "пошукай новини України"
        ]


class ApplicationPlugin(CommandPlugin):
    @property
    def name(self) -> str:
        return "application"

    @property
    def description(self) -> str:
        return "Запускає програми та додатки"

    @property
    def version(self) -> str:
        return "1.0.0"

    def can_handle(self, text: str, context: Dict[str, Any] = None) -> bool:
        text_lower = text.lower()
        keywords = ['запусти', 'відкрий', 'включи', 'стартуй']
        return any(keyword in text_lower for keyword in keywords)

    def execute(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        import subprocess
        import os

        # Мапа популярних програм
        app_map = {
            'блокнот': 'notepad.exe',
            'калькулятор': 'calc.exe',
            'пейнт': 'mspaint.exe',
            'провідник': 'explorer.exe',
            'chrome': 'chrome.exe',
            'firefox': 'firefox.exe',
            'код': 'code.exe',
            'vs code': 'code.exe',
            'visual studio': 'devenv.exe'
        }

        text_lower = text.lower()

        # Шукаємо відповідність в мапі
        for app_name, executable in app_map.items():
            if app_name in text_lower:
                try:
                    subprocess.Popen([executable])
                    return {
                        'success': True,
                        'message': f'Запускаю {app_name}',
                        'data': {'executable': executable}
                    }
                except FileNotFoundError:
                    return {
                        'success': False,
                        'message': f'Програма {app_name} не знайдена'
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'message': f'Помилка запуску {app_name}: {str(e)}'
                    }

        return {
            'success': False,
            'message': 'Програму не розпізнано'
        }

    def get_example_commands(self) -> List[str]:
        return [
            "запусти блокнот",
            "відкрий калькулятор",
            "включи VS Code"
        ]


class SystemVolumePlugin(CommandPlugin):
    @property
    def name(self) -> str:
        return "system_volume"

    @property
    def description(self) -> str:
        return "Керує системною гучністю"

    @property
    def version(self) -> str:
        return "1.0.0"

    def can_handle(self, text: str, context: Dict[str, Any] = None) -> bool:
        text_lower = text.lower()
        volume_keywords = ['гучність', 'звук', 'volume']
        level_keywords = ['%', 'відсотк', 'процент'] + [str(i) for i in range(0, 101)]

        has_volume = any(keyword in text_lower for keyword in volume_keywords)
        has_level = any(keyword in text_lower for keyword in level_keywords)

        return has_volume and has_level

    def execute(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            # Витягуємо рівень гучності з тексту
            level = self._extract_volume_level(text)

            if level is None:
                return {
                    'success': False,
                    'message': 'Не вдалося розпізнати рівень гучності'
                }

            # Встановлюємо гучність
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)

            return {
                'success': True,
                'message': f'Встановлено гучність на {level}%',
                'data': {'level': level}
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Помилка зміни гучності: {str(e)}'
            }

    def _extract_volume_level(self, text: str) -> Optional[int]:
        """Витягує рівень гучності з тексту."""
        import re

        # Шукаємо числа в тексті
        numbers = re.findall(r'\d+', text)

        for num_str in numbers:
            num = int(num_str)
            if 0 <= num <= 100:
                return num

        return None

    def get_example_commands(self) -> List[str]:
        return [
            "встанови гучність 50 відсотків",
            "звук на 75%",
            "гучність 30"
        ]


class AppVolumePlugin(CommandPlugin):
    @property
    def name(self) -> str:
        return "app_volume"

    @property
    def description(self) -> str:
        return "Керує гучністю активного додатку"

    @property
    def version(self) -> str:
        return "1.0.0"

    def can_handle(self, text: str, context: Dict[str, Any] = None) -> bool:
        text_lower = text.lower()
        app_keywords = ['програм', 'додат', 'аплікац']
        volume_keywords = ['гучність', 'звук']

        has_app = any(keyword in text_lower for keyword in app_keywords)
        has_volume = any(keyword in text_lower for keyword in volume_keywords)

        return has_app and has_volume

    def execute(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        try:
            from pycaw.pycaw import AudioUtilities
            import win32gui
            import win32process

            level = self._extract_volume_level(text)

            if level is None:
                return {
                    'success': False,
                    'message': 'Не вдалося розпізнати рівень гучності'
                }

            # Отримуємо PID активного вікна
            pid = win32process.GetWindowThreadProcessId(win32gui.GetForegroundWindow())[-1]

            # Знаходимо аудіо сесію для цього процесу
            sessions = AudioUtilities.GetAllSessions()
            target_session = None

            for session in sessions:
                if session.Process and session.Process.pid == pid:
                    target_session = session
                    break

            if target_session:
                volume = target_session.SimpleAudioVolume
                volume.SetMasterVolume(level / 100.0, None)

                return {
                    'success': True,
                    'message': f"Встановлено гучність для '{target_session.Process.name()}' на {level}%",
                    'data': {'level': level, 'app': target_session.Process.name()}
                }
            else:
                return {
                    'success': False,
                    'message': 'Не знайдено аудіо-сесію для активного вікна'
                }

        except Exception as e:
            return {
                'success': False,
                'message': f'Помилка зміни гучності додатку: {str(e)}'
            }

    def _extract_volume_level(self, text: str) -> Optional[int]:
        """Витягує рівень гучності з тексту."""
        import re

        numbers = re.findall(r'\d+', text)

        for num_str in numbers:
            num = int(num_str)
            if 0 <= num <= 100:
                return num

        return None

    def get_example_commands(self) -> List[str]:
        return [
            "гучність програми 50%",
            "звук додатку 75"
        ]


class ScriptPlugin(CommandPlugin):
    @property
    def name(self) -> str:
        return "script"

    @property
    def description(self) -> str:
        return "Виконує bash/batch скрипти"

    @property
    def version(self) -> str:
        return "1.0.0"

    def can_handle(self, text: str, context: Dict[str, Any] = None) -> bool:
        text_lower = text.lower()
        keywords = ['скрипт', 'виконай', 'запусти скрипт']
        return any(keyword in text_lower for keyword in keywords)

    def execute(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        import subprocess
        import os

        # В реальній імплементації тут мала б бути логіка
        # пошуку скрипту за назвою в папці scripts/
        return {
            'success': False,
            'message': 'Функція скриптів поки не реалізована'
        }

    def get_example_commands(self) -> List[str]:
        return [
            "запусти скрипт backup",
            "виконай clean_temp"
        ]