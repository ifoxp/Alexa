# smart_plugin_manager.py
import os
import sys
import importlib.util
import inspect
from typing import Dict, List, Any, Optional
from plugins.base_plugin import SmartPlugin
from logger_config import get_logger

logger = get_logger('smart_plugin_manager')


def discover_plugins() -> List[type]:
    """Автоматично знаходить всі плагіни в папці plugins/"""
    plugin_classes = []

    # Визначаємо папку plugins
    if hasattr(sys, '_MEIPASS'):
        # Запакований exe
        plugins_dir = os.path.join(sys._MEIPASS, 'plugins')
    else:
        # Розробка
        plugins_dir = os.path.join(os.path.dirname(__file__), 'plugins')

    logger.info(f"Scanning plugins directory: {plugins_dir}")

    if not os.path.exists(plugins_dir):
        logger.warning(f"Plugins directory not found: {plugins_dir}")
        return plugin_classes

    # Сканування всіх .py файлів в папці plugins
    for filename in os.listdir(plugins_dir):
        if filename.endswith('.py') and not filename.startswith('_'):
            plugin_path = os.path.join(plugins_dir, filename)
            module_name = filename[:-3]  # видаляємо .py

            try:
                logger.debug(f"Loading plugin file: {filename}")

                # Завантажуємо модуль
                spec = importlib.util.spec_from_file_location(module_name, plugin_path)
                if spec is None or spec.loader is None:
                    logger.warning(f"Could not load spec for {filename}")
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Знаходимо всі класи які наслідують SmartPlugin
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (obj != SmartPlugin and
                        issubclass(obj, SmartPlugin) and
                        obj.__module__ == module_name):
                        plugin_classes.append(obj)
                        logger.debug(f"Found plugin class: {name} in {filename}")

            except Exception as e:
                logger.error(f"Failed to load plugin file {filename}: {str(e)}")
                continue

    logger.info(f"Discovered {len(plugin_classes)} plugin classes")
    return plugin_classes


class SmartPluginManager:
    """Менеджер розумних плагінів для GPT-інтеграції."""

    def __init__(self):
        self.plugins: Dict[str, SmartPlugin] = {}
        self.load_plugins()

    def load_plugins(self):
        """Завантажує всі доступні плагіни."""
        # Тимчасово використовуємо стару систему для стабільності
        try:
            from plugins import AVAILABLE_PLUGINS
            available_plugins = AVAILABLE_PLUGINS
            logger.info("Using legacy plugin loading system")
        except ImportError:
            # Якщо не вдається - використовуємо автозавантаження
            available_plugins = discover_plugins()
            logger.info("Using auto-discovery plugin loading system")

        logger.info(f"Starting to load {len(available_plugins)} plugin classes", extra={
            'plugin_classes': [cls.__name__ for cls in available_plugins]
        })

        for plugin_class in available_plugins:
            try:
                logger.debug(f"Instantiating plugin class: {plugin_class.__name__}")
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

                logger.debug(f"Plugin {plugin_class.__name__}: name='{plugin_name}', description='{plugin_description[:50]}...'")

                self.plugins[plugin_name] = plugin_instance
                logger.info(f"Successfully loaded plugin: {plugin_name}")

            except Exception as e:
                import traceback
                logger.error(f"Failed to load plugin {plugin_class.__name__}", extra={
                    'error': str(e),
                    'error_type': type(e).__name__,
                    'traceback': traceback.format_exc()
                })

        logger.info(f"Plugin loading completed: {len(self.plugins)}/{len(AVAILABLE_PLUGINS)} plugins loaded", extra={
            'loaded_plugins': list(self.plugins.keys())
        })

    def get_plugins_summary(self) -> List[Dict[str, Any]]:
        """
        Повертає короткий список плагінів для GPT (етап 1).

        Returns:
            List з short info про кожен плагін
        """
        plugins_summary = []

        logger.info(f"Getting summary for {len(self.plugins)} plugins", extra={
            'plugin_names': list(self.plugins.keys())
        })

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
        logger.info(f"Successfully created summaries for {len(plugins_summary)} plugins")
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
            logger.info(f"Executing {plugin_name}.{command_name}", extra={'params': kwargs})
            result = await plugin.execute_command(command_name, **kwargs)

            if result.get("success"):
                logger.info(f"Successfully executed {plugin_name}.{command_name}")
            else:
                logger.warning(f"Command failed: {plugin_name}.{command_name}", extra={'message': result.get('message')})

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