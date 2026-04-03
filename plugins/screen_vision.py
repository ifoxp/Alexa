import os
import json
import asyncio
import pyautogui
import mss
import mss.tools
import pyperclip
from typing import Dict, Any, Tuple
from .base_plugin import SmartPlugin
import smart_ai
from google.genai import types

class ScreenVisionPlugin(SmartPlugin):
    """Плагін для візуального аналізу екрана: 'бачить' помилки, аніме, текст і працює з буфером."""

    def __init__(self):
        super().__init__()
        # ⚠️ ЗМІНА 1: Більше не тримаємо глобальний self.sct,
        # щоб уникнути помилок потоків на Windows.

    @property
    def name(self) -> str:
        return "screen_vision"

    @property
    def description(self) -> str:
        return "Візуальний аналіз екрана. Використовуй для запитів: 'що на екрані', 'яка помилка', 'що за мультик/аніме', 'прочитай текст тут'."

    @property
    def commands(self) -> Dict[str, str]:
        return {
            "analyze_screen": "Проаналізувати активний монітор. Передай суть запиту користувача (наприклад: 'знайди мультик', 'поясни помилку') у параметр 'value'."
        }

    def _take_screenshot_blocking(self, screenshot_path: str) -> Tuple[bool, str]:
        """
        Синхронна функція для визначення монітора та створення скріншота.
        Використовує MSS через контекстний менеджер для стабільності на Windows.
        """
        try:
            # ⚠️ ЗМІНА 2: Створюємо MSS екземпляр тільки тут, в окремому потоці,
            # і тільки через 'with', щоб він автоматично закривався.
            with mss.mss() as sct:
                # 1. Знаходимо координати мишки
                # (pyautogui теж блокуюча, тому їй місце в цьому потоці)
                x, y = pyautogui.position()
                print(f"[VISION DEBUG] Мишка за координатами: {x}, {y}")

                # 2. Знаходимо монітор під мишкою
                target_monitor = None
                # sct.monitors[0] - це весь робочий стіл, пропускаємо
                for i, monitor in enumerate(sct.monitors[1:], 1):
                    if (monitor["left"] <= x <= monitor["left"] + monitor["width"] and
                        monitor["top"] <= y <= monitor["top"] + monitor["height"]):
                        print(f"[VISION DEBUG] Знайдено монітор №{i}")
                        target_monitor = monitor
                        break
                
                # Fallback на головний монітор, якщо не знайшли
                if not target_monitor:
                    target_monitor = sct.monitors[1]
                
                # 3. Робимо скріншот
                sct_img = sct.grab(target_monitor)
                
                # 4. Зберігаємо у PNG
                mss.tools.to_png(sct_img.rgb, sct_img.size, output=screenshot_path)
                
                return True, f"Скріншот монітора {i if target_monitor else 1} створено"

        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"[VISION ERROR] Помилка у блокуючому потоці:\n{error_details}")
            return False, str(e)

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        """Виконує команду плагіна."""
        try:
            print(f"[VISION] execute: command={command_name}, kwargs={kwargs}")

            if command_name == "analyze_screen":
                user_request = kwargs.get("value", "опиши, що ти бачиш")
                print(f"[VISION] user_request: '{user_request}'")

                screenshot_path = "temp_screenshot.png"
                print(f"[VISION] taking screenshot in thread...")

                success, details = await asyncio.to_thread(self._take_screenshot_blocking, screenshot_path)

                if not success or not os.path.exists(screenshot_path):
                    print(f"[VISION] screenshot failed: {details}")
                    return {"success": False, "message": f"Помилка створення скріншота: {details}"}

                print(f"[VISION] {details}")

                # 2. Відправляємо запит до Gemini Vision
                if not smart_ai.smart_assistant:
                    return {"success": False, "message": "ШІ асистент не ініціалізований."}

                visual_instruction = """Ти — JARVIS, розумний візуальний асистент. Тобі надано скріншот екрана. Проаналізуй його згідно з запитом.

КРИТИЧНІ ПРАВИЛА:
1. ФОРМАТ: ЗАВЖДИ повертай виключно JSON. Жодного зайвого тексту.
2. МОВА: АБСОЛЮТНО ВСЕ має бути українською мовою. Назви серіалів, мультиків, ігор чи фільмів адаптуй або перекладай українською (наприклад, "Дивовижний цифровий цирк", а не "The Amazing Digital Circus"). Виняток — лише сирий код помилок або специфічні IT-терміни, які не перекладаються.
3. ПОЛЯ JSON:
   * `clipboard_text` (опціонально): Текст, який буде скопійовано. 
     - [АДАПТАЦІЯ ТОНУ]: Якщо користувач просить написати відповідь/повідомлення на основі екрана, ПІДЛАШТОВУЙ ТОН! Якщо бачиш серйозний email — пиши строго і по-діловому. Якщо це переписка в месенджері з друзями — пиши просто, неформально, можна з гумором, як "дружбан". 
     - Якщо це пошук фільму/помилки — просто поклади сюди українську назву або суть помилки.
   * `speak_text`: Текст, який ти скажеш вголос. Коротко, по суті. 
     - [ЗВ'ЯЗОК З БУФЕРОМ]: Якщо ти додав щось у `clipboard_text`, ти ЗОБОВ'ЯЗАНИЙ чітко сказати про це тут. 
     - Приклади правильної озвучки: "Це мультик Дивовижний цифровий цирк, я вже закинув назву у ваш буфер обміну", або "Я підготував серйозну відповідь директору, текст вже в буфері, можете вставляти", або "Це помилка бази даних, я скопіював її код для вас".
"""

                combined_prompt = f"{visual_instruction}\n\nЗАПИТ КОРИСТУВАЧА: {user_request}"
                
                print(f"[VISION] sending to Gemini Vision: '{user_request}'")

                try:
                    with open(screenshot_path, 'rb') as f:
                        image_data = f.read()

                    contents = [
                        types.Content(role="user", parts=[
                            types.Part.from_text(text=combined_prompt),
                            types.Part.from_bytes(data=image_data, mime_type="image/png")
                        ])
                    ]
                    response = await asyncio.to_thread(
                        smart_ai.smart_assistant.client.models.generate_content,
                        model=smart_ai.smart_assistant.plugin_model,
                        config=types.GenerateContentConfig(
                            temperature=0.4,
                            response_mime_type="application/json"
                        ),
                        contents=contents
                    )
                except Exception as e:
                    print(f"[ERROR] Помилка запиту до Gemini Vision API: {e}")
                    return {"success": False, "message": f"Помилка аналізу в Gemini API: {str(e)}"}
                finally:
                    # Видаляємо тимчасовий скріншот у будь-якому випадку
                    if os.path.exists(screenshot_path):
                        os.remove(screenshot_path)
                        print(f"[VISION] temp screenshot deleted")

                final_response_text = response.text.strip()
                print(f"[VISION] Gemini response: {final_response_text}")

                try:
                    data = json.loads(final_response_text)
                    speak_text = data.get("speak_text", "Я проаналізував екран, сер.")
                    clipboard_text = data.get("clipboard_text", "")

                    # 4. Взаємодія з буфером обміну
                    plugin_message_suffix = ""
                    if clipboard_text:
                        pyperclip.copy(clipboard_text)
                        print(f"[VISION] copied to clipboard: '{clipboard_text[:80]}'")
                        plugin_message_suffix = " (Текст скопійовано в буфер)."

                    print(f"[VISION] speak_text: '{speak_text}'")

                    return {
                        "success": True,
                        "message": f"Аналіз екрана завершено{plugin_message_suffix}.",
                        "speak_text": speak_text,
                        "clipboard_text": clipboard_text
                    }

                except json.JSONDecodeError:
                    print(f"[VISION] failed to parse JSON from Gemini: {final_response_text[:200]}")
                    return {"success": False, "message": "Помилка формату візуальних даних від API."}

            else:
                return {"success": False, "message": f"Невідома команда: {command_name}"}

        except Exception as e:
            print(f"[CRITICAL ERROR] Загальна помилка Screen Vision Plugin: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"Внутрішня помилка візуального аналізу: {str(e)}"}