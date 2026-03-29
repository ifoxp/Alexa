import os
import json
import asyncio
from collections import deque
from datetime import datetime
from pathlib import Path


def _get_logs_dir() -> Path:
    import sys
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
    else:
        base_dir = Path(__file__).parent
    return base_dir / "logs"


def _ts() -> str:
    return datetime.now().strftime("[%d.%m.%y %H:%M:%S]")


SEP = "=" * 48


class CommandLogger:
    def __init__(self):
        self.lock = asyncio.Lock()
        # Зберігаємо 5 останніх AI промптів (system + user + response)
        self._ai_history: deque = deque(maxlen=5)

    def _commands_path(self) -> Path:
        return _get_logs_dir() / "commands.txt"

    def _ai_path(self) -> Path:
        return _get_logs_dir() / "commands_ai.txt"

    async def log_command(self, user_command: str, ai_result: dict):
        """Логує команду в commands.txt (читабельний формат)."""
        async with self.lock:
            try:
                ts = _ts()
                is_command = ai_result.get("success", False)
                jarvis_response = ai_result.get("jarvis_response", ai_result.get("quick_response", "—"))
                execution_plan = ai_result.get("execution_plan", [])

                plugins_lines = ""
                for step in execution_plan:
                    plugin = step.get("plugin", "?")
                    command = step.get("command", "?")
                    value = step.get("params", {}).get("value", "")
                    level = step.get("params", {}).get("level", "")
                    params_str = ""
                    if value:
                        params_str += value
                    if level:
                        params_str += f" | рівень: {level}"
                    if params_str:
                        plugins_lines += f"  {plugin} -> {command} : {params_str}\n"
                    else:
                        plugins_lines += f"  {plugin} -> {command}\n"

                if not plugins_lines:
                    plugins_lines = "  (немає)\n"

                entry = (
                    f"\n{SEP}\n"
                    f"{ts}\n"
                    f"Команда: {user_command}\n"
                    f"Це команда: {str(is_command).lower()}\n"
                    f"Плагіни:\n{plugins_lines}"
                    f"Відповідь Jarvis: '{jarvis_response}'\n"
                    f"{SEP}\n"
                )

                path = self._commands_path()
                path.parent.mkdir(exist_ok=True)
                with open(path, 'a', encoding='utf-8') as f:
                    f.write(entry)

            except Exception as e:
                print(f"[CommandLogger] Помилка запису commands.txt: {e}")

    def log_ai_exchange(self, system_prompt: str, user_prompt: str, raw_response):
        """Зберігає AI обмін в пам'яті (5 останніх) і записує в commands_ai.txt."""
        try:
            ts = _ts()

            # Серіалізуємо відповідь
            try:
                response_parts = []
                if hasattr(raw_response, 'candidates') and raw_response.candidates:
                    for part in raw_response.candidates[0].content.parts:
                        if part.function_call:
                            response_parts.append({
                                "function_call": part.function_call.name,
                                "args": dict(part.function_call.args)
                            })
                        elif hasattr(part, 'text') and part.text:
                            response_parts.append({"text": part.text})
                response_str = json.dumps(response_parts, ensure_ascii=False, indent=2)
            except Exception:
                response_str = str(raw_response)

            record = {
                "ts": ts,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response": response_str
            }
            self._ai_history.append(record)

            # Записуємо в файл
            entry = (
                f"\n{SEP}\n"
                f"{ts}\n"
                f"--- SYSTEM PROMPT ---\n{system_prompt}\n\n"
                f"--- USER PROMPT ---\n{user_prompt}\n\n"
                f"--- ВІДПОВІДЬ GEMINI ---\n{response_str}\n"
                f"{SEP}\n"
            )

            path = self._ai_path()
            path.parent.mkdir(exist_ok=True)

            # Перезаписуємо файл тільки з 5 останніми записами
            existing = self._read_ai_file()
            existing.append(entry)
            if len(existing) > 5:
                existing = existing[-5:]

            with open(path, 'w', encoding='utf-8') as f:
                f.write("".join(existing))

        except Exception as e:
            print(f"[CommandLogger] Помилка запису commands_ai.txt: {e}")

    def _read_ai_file(self) -> list:
        """Читає існуючі записи з commands_ai.txt."""
        path = self._ai_path()
        if not path.exists():
            return []
        try:
            content = path.read_text(encoding='utf-8')
            # Розбиваємо по сепаратору
            parts = content.split(f"\n{SEP}\n")
            result = []
            for p in parts:
                stripped = p.strip()
                if stripped:
                    result.append(f"\n{SEP}\n{stripped}\n{SEP}\n")
            return result
        except Exception:
            return []

    def get_last_ai_exchanges(self) -> list:
        """Повертає 5 останніх AI обмінів з пам'яті."""
        return list(self._ai_history)


# Глобальний екземпляр
command_logger = CommandLogger()
