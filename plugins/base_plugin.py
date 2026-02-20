# base_plugin.py
import asyncio
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

    async def ask_gpt(self, prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> str:
        """
        Викликає GPT з власним промптом плагіна.

        Args:
            prompt: Промпт для GPT
            max_tokens: Максимум токенів
            temperature: Температура (креативність)

        Returns:
            Відповідь GPT або помилкове повідомлення
        """
        try:
            import smart_ai

            if not smart_ai.smart_assistant:
                return "GPT недоступний"

            response = await smart_ai.smart_assistant.client.chat.completions.create(
                model=smart_ai.smart_assistant.model,
                messages=[
                    {"role": "system", "content": f"Ти допомагаєш плагіну '{self.name}'. Відповідай українською мовою."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            self.log_error(f"GPT request failed", error=str(e))
            return f"Помилка запиту до GPT: {str(e)}"

    async def speak_text(self, text: str) -> bool:
        """
        Озвучує текст через TTS систему.

        Args:
            text: Текст для озвучування

        Returns:
            True якщо успішно, False якщо помилка
        """
        try:
            from audio_player import speak_text
            import config_manager as cfg

            config = cfg.load_config()
            await asyncio.to_thread(speak_text, text, config)
            return True

        except Exception as e:
            self.log_error(f"TTS failed for text: {text[:50]}...", error=str(e))
            return False

    async def ask_gpt_and_speak(self, prompt: str, max_tokens: int = 150, temperature: float = 0.7) -> Dict[str, Any]:
        """
        Комбінована функція: запитує GPT та озвучує відповідь.

        Args:
            prompt: Промпт для GPT
            max_tokens: Максимум токенів
            temperature: Температура

        Returns:
            {"success": bool, "text": str, "spoken": bool}
        """
        try:
            # Отримуємо відповідь від GPT
            gpt_response = await self.ask_gpt(prompt, max_tokens, temperature)

            if "Помилка" in gpt_response or "недоступний" in gpt_response:
                return {
                    "success": False,
                    "text": gpt_response,
                    "spoken": False
                }

            # Озвучуємо відповідь
            spoken_successfully = await self.speak_text(gpt_response)

            return {
                "success": True,
                "text": gpt_response,
                "spoken": spoken_successfully
            }

        except Exception as e:
            self.log_error(f"ask_gpt_and_speak failed", error=str(e))
            return {
                "success": False,
                "text": f"Помилка: {str(e)}",
                "spoken": False
            }