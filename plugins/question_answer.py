from typing import Dict, Any
from .base_plugin import SmartPlugin


class QuestionAnswerPlugin(SmartPlugin):
    """Плагін для відповідей на будь-які запитання користувача голосом."""

    @property
    def name(self) -> str:
        return "question_answer"

    @property
    def description(self) -> str:
        return (
            "Відповідає на будь-які запитання користувача. "
            "Використовуй ТІЛЬКИ коли користувач ставить пряме запитання і не потрібні інші плагіни — "
            "наприклад: 'що таке чорна діра', 'як працює квантовий комп'ютер', 'хто такий Шевченко', "
            "'яка столиця Франції'. НЕ використовуй для дій (відкрити, увімкнути, пошукати)."
        )

    @property
    def commands(self) -> Dict[str, str]:
        return {
            "answer": "Відповісти на запитання користувача голосом. Параметр question — текст запитання."
        }

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        if command_name != "answer":
            return {"success": False, "result": None, "message": f"Невідома команда: {command_name}"}

        question = kwargs.get("question") or kwargs.get("value", "")
        if not question:
            return {"success": False, "result": None, "message": "Запитання не передано"}

        self.log_info(f"Відповідаю на запитання: {question}")

        prompt = (
            f"Користувач запитав: «{question}»\n\n"
            "Дай коротку, чітку відповідь українською мовою. "
            "Текст буде озвучено голосом — без списків, без зірочок, без markdown. "
            "Максимум 3-4 речення."
        )

        result = await self.ask_gpt_and_speak(prompt, max_tokens=300, temperature=0.5)

        return {
            "success": result["success"],
            "result": result["text"],
            "message": result["text"],
        }
