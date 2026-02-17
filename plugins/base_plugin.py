# base_plugin.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from logger_config import get_logger

logger = get_logger('base_plugin')


class SmartPlugin(ABC):
    """Базовий клас для розумних плагінів з GPT інтеграцією."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Унікальне ім'я плагіна."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Короткий опис плагіна для GPT (1-2 речення)."""
        pass

    @property
    @abstractmethod
    def commands(self) -> Dict[str, str]:
        """
        Словник команд плагіна: {назва_функції: короткий_опис}
        Приклад: {
            "search_programs": "знайти програму по назві",
            "open_program": "відкрити програму за шляхом"
        }
        """
        pass

    @abstractmethod
    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        """
        Виконує команду плагіна.

        Args:
            command_name: назва команди з commands
            **kwargs: параметри команди

        Returns:
            {"success": bool, "result": Any, "message": str}
        """
        pass

    def get_plugin_info(self) -> Dict[str, Any]:
        """Повертає інформацію про плагін для GPT."""
        return {
            "name": self.name,
            "description": self.description,
            "commands": self.commands
        }

    def log_info(self, message: str, **kwargs):
        """Логування інформації плагіна."""
        logger.info(f"[{self.name}] {message}", extra=kwargs)

    def log_error(self, message: str, **kwargs):
        """Логування помилок плагіна."""
        logger.error(f"[{self.name}] {message}", extra=kwargs)