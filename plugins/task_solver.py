import os
import json
import asyncio
import pyautogui
import mss
import mss.tools
import pyperclip
import tempfile
import uuid
from typing import Dict, Any, Tuple
from .base_plugin import SmartPlugin
import smart_ai
from google.genai import types


class TaskSolverPlugin(SmartPlugin):
    """Плагін для вирішення задач, тестів і запитань з екрана: бачить завдання → дає коротку відповідь → копіює у буфер."""

    def __init__(self):
        super().__init__()

    @property
    def name(self) -> str:
        return "task_solver"

    @property
    def description(self) -> str:
        return "Аналізує екран і вирішує задачі, тести, запитання. Використовуй для: 'виріши задачу', 'відповідь на питання', 'що тут написати', 'вибери варіант'."

    @property
    def commands(self) -> Dict[str, str]:
        return {
            "solve_task": "Проаналізувати екран і вирішити задачу/тест/запитання. Передай суть запиту у параметр 'value' (наприклад: 'виріши', 'дай відповідь', 'вибери правильний варіант')."
        }

    def _take_screenshot_blocking(self, screenshot_path: str) -> Tuple[bool, str]:
        """Синхронна функція: визначає монітор під мишкою і робить скріншот."""
        try:
            with mss.mss() as sct:
                x, y = pyautogui.position()
                print(f"[TASK_SOLVER DEBUG] Мишка: {x}, {y}")

                target_monitor = None
                monitor_index = 1
                for i, monitor in enumerate(sct.monitors[1:], 1):
                    if (monitor["left"] <= x <= monitor["left"] + monitor["width"] and
                            monitor["top"] <= y <= monitor["top"] + monitor["height"]):
                        print(f"[TASK_SOLVER DEBUG] Монітор №{i}")
                        target_monitor = monitor
                        monitor_index = i
                        break

                if not target_monitor:
                    target_monitor = sct.monitors[1]

                sct_img = sct.grab(target_monitor)
                mss.tools.to_png(sct_img.rgb, sct_img.size, output=screenshot_path)

                return True, f"Скріншот монітора {monitor_index} створено"

        except Exception as e:
            import traceback
            print(f"[TASK_SOLVER ERROR] Помилка скріншота:\n{traceback.format_exc()}")
            return False, str(e)

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        """Виконує команду плагіна."""
        try:
            print(f"[TASK_SOLVER] execute: command={command_name}, kwargs={kwargs}")

            if command_name == "solve_task":
                user_request = kwargs.get("value", "виріши задачу або дай відповідь на питання")
                print(f"[TASK_SOLVER] user_request: '{user_request}'")

                temp_dir = tempfile.gettempdir()
                unique_filename = f"task_screenshot_{uuid.uuid4().hex}.png"
                screenshot_path = os.path.join(temp_dir, unique_filename)
                
                print(f"[TASK_SOLVER] роблю скріншот у {screenshot_path}...")

                success, details = await asyncio.to_thread(self._take_screenshot_blocking, screenshot_path)

                if not success or not os.path.exists(screenshot_path):
                    print(f"[TASK_SOLVER] скріншот не вдався: {details}")
                    return {"success": False, "message": f"Помилка створення скріншота: {details}"}

                print(f"[TASK_SOLVER] {details}")

                if not smart_ai.smart_assistant:
                    return {"success": False, "message": "ШІ асистент не ініціалізований."}

                instruction = """Ти відповідаєш на питання з тесту або завдання. Пишеш як звичайний 22-річний студент — по-людськи, без канцеляриту, без офіційного тону. Не використовуй фрази типу "Відповідь:", "Зафіксовано", "Зазначимо". Просто пишеш як пишуть люди.

КРИТИЧНІ ПРАВИЛА:
1. ФОРМАТ: Повертай ВИКЛЮЧНО JSON. Жодного зайвого тексту поза JSON.
2. МОВА: Відповідь — українською (або тією мовою, якою написане завдання).
3. НЕ розкривай абревіатури у дужках — якщо написав DI, не пиши після "(Dependency Injection)". Якщо написав ORM — просто ORM.
4. НЕ пиши повні назви методів якщо вони довгі — пиши як студент по пам'яті: .Include(), .ThenInclude() — ок. Але не "метод System.Linq.Enumerable.Include<TSource>".
5. Починай відповідь зі слова "Відповідь" на новому рядку перед поясненням — це маркер для форми.
6. НЕ звучи як ChatGPT або документація. Звучи як людина.

ВИЗНАЧЕННЯ ТИПУ ЕКРАНА:

A) ДЕКІЛЬКА ЗАВДАНЬ/ПИТАНЬ на екрані:
   Структура JSON:
   {
     "mode": "multi",
     "tasks": [
       {"id": "Завдання 18", "answer": "А — текст варіанта"},
       {"id": "Завдання 19", "answer": "C++"},
       ...
     ],
     "answer": "Завдання 18: А\nЗавдання 19: C++\n...",
     "speak_text": "Завдання 18 — А, завдання 19 — C++. Всі відповіді скопійовано в буфер."
   }
   - Для кожного завдання вкажи його номер/назву і відповідь
   - У полі answer — всі відповіді через новий рядок (це піде в буфер)

B) ОДНЕ ЗАВДАННЯ — КОД (програмування):
   Структура JSON:
   {
     "mode": "code",
     "answer": "повний робочий код без коментарів, з правильними відступами та переносами рядків",
     "speak_text": "Ось код. Мова: [мова]. Скопійовано в буфер."
   }
   - answer: ТІЛЬКИ код, без пояснень, без ``` обгортки, без коментарів
   - Правильні відступи і переноси рядків обов'язкові

C) ОДНЕ ЗАВДАННЯ — ТЕКСТОВА ВІДПОВІДЬ (пояснення, теорія тощо):
   Структура JSON:
   {
     "mode": "single",
     "answer": "Відповідь\n[текст відповіді написаний по-людськи, як студент пише від руки. Без зайвого — тільки суть.]",
     "speak_text": "Коротко про що відповідь(або зачитай правильний варіант відповіді). і скажи що вона Скопійована в буфер."
   }
   - Перший рядок answer завжди: "Відповідь" (окремий рядок)
   - Далі — пояснення живою мовою, без шаблонних зворотів
   - Для тесту з варіантами: літера + текст варіанта
   - Для числа: число і одиниці якщо треба

ПРАВИЛА ДЛЯ speak_text (всі режими):
- Максимум 2 речення
- Завжди згадай що скопійовано в буфер"""

                combined_prompt = f"{instruction}\n\nЗАПИТ: {user_request}"

                print(f"[TASK_SOLVER] відправляю до Gemini Vision...")

                try:
                    with open(screenshot_path, 'rb') as f:
                        image_data = f.read()

                    contents = [
                        types.Content(role="user", parts=[
                            types.Part.from_text(text=combined_prompt),
                            types.Part.from_bytes(data=image_data, mime_type="image/png")
                        ])
                    ]

                    fallback_models = [
                        smart_ai.smart_assistant.plugin_model, 
                        "gemini-3.1-flash",
                        "gemini-3.0-flash",
                        "gemini-3-flash-preview"
                    ]

                    response = None
                    last_error = None
                    
                    for model_name in fallback_models:
                        try:
                            print(f"[TASK_SOLVER] Відправляю запит на модель: {model_name}...")
                            response = await asyncio.to_thread(
                                smart_ai.smart_assistant.client.models.generate_content,
                                model=model_name,
                                config=types.GenerateContentConfig(
                                    temperature=0.2,
                                    response_mime_type="application/json"
                                ),
                                contents=contents
                            )
                            break 
                        except Exception as e:
                            last_error = e
                            print(f"[TASK_SOLVER] Помилка на моделі {model_name}: {e}")
                            
                            print("[TASK_SOLVER] Миттєве перемикання на резервну модель...")
                            await asyncio.sleep(0.5) 

                    if response is None:
                        print(f"[TASK_SOLVER ERROR] Всі резервні моделі недоступні: {last_error}")
                        return {"success": False, "message": "Всі сервери Google перевантажені, спробуй ще раз"}

                except Exception as e:
                    print(f"[TASK_SOLVER ERROR] Gemini API помилка: {e}")
                    return {"success": False, "message": f"Помилка аналізу Gemini API: {str(e)}"}
                finally:
                    if os.path.exists(screenshot_path):
                        os.remove(screenshot_path)
                        print(f"[TASK_SOLVER] тимчасовий скріншот видалено")

                final_response_text = response.text.strip()
                
                if final_response_text.startswith("```json"):
                    final_response_text = final_response_text[7:]
                elif final_response_text.startswith("```"):
                    final_response_text = final_response_text[3:]
                
                if final_response_text.endswith("```"):
                    final_response_text = final_response_text[:-3]
                    
                final_response_text = final_response_text.strip()

                print(f"[TASK_SOLVER] Очищена Gemini відповідь: {final_response_text}")

                try:
                    data = json.loads(final_response_text)
                    answer = data.get("answer", "")
                    speak_text = data.get("speak_text", "Я проаналізував завдання.")

                    if answer:
                        pyperclip.copy(str(answer))
                        print(f"[TASK_SOLVER] скопійовано у буфер: '{str(answer)[:80]}'")

                    print(f"[TASK_SOLVER] speak_text: '{speak_text}'")

                    return {
                        "success": True,
                        "message": f"Задачу вирішено. Відповідь скопійовано у буфер.",
                        "speak_text": speak_text,
                        "answer": answer
                    }

                except json.JSONDecodeError:
                    print(f"[TASK_SOLVER] не вдалося розпарсити JSON: {final_response_text[:200]}")
                    return {"success": False, "message": "Помилка формату відповіді від API."}

            else:
                return {"success": False, "message": f"Невідома команда: {command_name}"}

        except Exception as e:
            print(f"[TASK_SOLVER CRITICAL ERROR] {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"Внутрішня помилка task_solver: {str(e)}"}