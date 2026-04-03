import webbrowser
import urllib.parse
from typing import Dict, Any
from .base_plugin import SmartPlugin
import smart_ai


class MovieRecommendationsPlugin(SmartPlugin):
    """Плагін для динамічних рекомендацій фільмів/аніме/серіалів через GPT з пошуком на uakino."""

    @property
    def name(self) -> str:
        return "movie_recommendations"

    @property
    def description(self) -> str:
        return "Рекомендує фільми, серіали та аніме на основі запиту або настрою, генеруючи унікальні описи та автоматично відкриваючи їх для перегляду на uakino."

    @property
    def commands(self) -> Dict[str, str]:
        # Ми максимально спростили команди, адже GPT сам розбереться, що шукати
        return {
            "recommend_movie": "Порекомендувати фільм/серіал/аніме (можна вказати жанр, настрій або просто випадково)",
            "search_movie": "Знайти та відкрити конкретний фільм/серіал/аніме за назвою"
        }

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        """Виконує команду плагіна."""
        try:
            print(f"[MOVIE_REC] execute: command={command_name}, kwargs={kwargs}")

            if command_name == "recommend_movie":
                # Отримуємо запит, жанр або настрій
                genre_or_mood = kwargs.get("value") or kwargs.get("genre") or kwargs.get("mood", "на твій смак")
                print(f"[MOVIE_REC] recommend request: '{genre_or_mood}'")
                return await self._recommend_movie(genre_or_mood)

            elif command_name == "search_movie":
                movie_name = kwargs.get("value") or kwargs.get("movie", "")
                print(f"[MOVIE_REC] direct search request: '{movie_name}'")
                return await self._search_movie(movie_name)

            else:
                print(f"[MOVIE_REC] unknown command: {command_name}")
                return {
                    "success": False,
                    "result": None,
                    "message": f"Невідома команда: {command_name}"
                }

        except Exception as e:
            print(f"[MOVIE_REC] error in execute_command: {e}")
            return {
                "success": False,
                "result": None,
                "message": f"Помилка виконання команди: {str(e)}"
            }

    async def _recommend_movie(self, request_text: str) -> Dict[str, Any]:
        """Запитує GPT про рекомендацію, парсить назву та відкриває пошук."""
        if not smart_ai.smart_assistant:
            # Якщо GPT відключений, просто шукаємо як звичайний текст
            print(f"[MOVIE_REC] GPT unavailable, falling back to direct search for: '{request_text}'")
            return await self._search_movie(request_text)

        try:
            # Змушуємо GPT думати і повертати інформацію у строгому форматі
            prompt = f"""Ти - кінокритик і голосовий асистент Jarvis.
Користувач просить порадити щось подивитися. Запит: "{request_text}".
Якщо запит загальний, можеш порадити якісний екшн, цікаве аніме (в стилі Сім смертних гріхів) або щось з цікавою мультиплікацією/гумором (в стилі Хазбін Готель).
ЯКЩО КОРИСТУВАЧ ПРОСИЛЬ ФІЛЬМ ТО ШУКАЙ САМЕ ФІЛЬМ, ЯКЩО СЕРІАЛ - ТО СЕРІАЛ, ЯКЩО АНІМЕ - ТО АНІМЕ. НЕ ПОВЕРТАЙ СУПЕРЗАГАЛЬНІ РЕКОМЕНДАЦІЇ НА КШТАЛТ "Щось цікаве". Якщо запит дуже розмитий, можеш просто порадити щось на свій смак, але все одно вказуй конкретну назву.
ОБОВ'ЯЗКОВИЙ ФОРМАТ ВІДПОВІДІ (строго 2 рядки):
Назва: [Тільки точна назва фільму/серіалу/аніме українською]
Опис: [Обов'язково напиши назву вибраного фільму/серіалу/аніме і напиши 2-3 речення про те, чому це круто і варто уваги. Без банальних фраз "Я рекомендую". Природна розповідь, що інтригує. В кінці додай "сер".]"""

            print(f"[MOVIE_REC] sending prompt to GPT (first 80 chars): '{prompt[:80].strip()}'")
            gpt_reply = await self.ask_gpt(prompt, max_tokens=250, temperature=0.8)
            print(f"[MOVIE_REC] GPT raw reply:\n{gpt_reply}")

            # Витягуємо назву та опис із відповіді GPT
            title = ""
            description = ""
            for line in gpt_reply.split('\n'):
                if line.startswith("Назва:"):
                    title = line.replace("Назва:", "").strip()
                elif line.startswith("Опис:"):
                    description = line.replace("Опис:", "").strip()

            print(f"[MOVIE_REC] parsed title: '{title}'")
            print(f"[MOVIE_REC] parsed description: '{description}'")

            # Якщо GPT чомусь збився з формату, рятуємо ситуацію
            if not title or not description:
                print(f"[MOVIE_REC] GPT reply did not match expected format, using fallback values")
                title = request_text if request_text != "на твій смак" else "Щось цікаве"
                description = gpt_reply if gpt_reply else "Ось що я знайшов, сер."

            # Відкриваємо пошук на uakino
            return await self._search_and_open_uakino(title, description)

        except Exception as e:
            print(f"[MOVIE_REC] GPT recommendation failed: {e}")
            return await self._search_and_open_uakino("Цікавий фільм", "Відкриваю сторінку з фільмами, сер.")

    async def _search_movie(self, movie_name: str) -> Dict[str, Any]:
        """Для прямого пошуку конкретного фільму, якщо користувач вже знає, що хоче."""
        if not movie_name:
            return {"success": False, "result": None, "message": "Назва фільму не може бути пустою"}

        description = f"Відкриваю {movie_name} для перегляду, сер."
        return await self._search_and_open_uakino(movie_name, description)

    async def _search_and_open_uakino(self, movie_name: str, speak_text: str) -> Dict[str, Any]:
        """Формує пошуковий запит 'дивитися на uakino' і відкриває Google."""
        try:
            # Додаємо ключові слова до назви
            search_query = f"{movie_name} дивитися на uakino"
            encoded_query = urllib.parse.quote(search_query)

            # Шукаємо через Google (він найкраще знаходить правильне посилання на uakino, навіть якщо є помилка в назві)
            google_url = f"https://www.google.com/search?q={encoded_query}"

            webbrowser.open(google_url)
            print(f"[MOVIE_REC] opened URL: {google_url}")
            print(f"[MOVIE_REC] speak_text: '{speak_text}'")

            return {
                "success": True,
                "result": {
                    "movie": movie_name,
                    "url": google_url
                },
                "message": f"Шукаю '{movie_name}' на uakino",
                "speak_text": speak_text # Тут буде красива розповідь від GPT!
            }
        except Exception as e:
            print(f"[MOVIE_REC] failed to open URL for '{movie_name}': {e}")
            return {
                "success": False,
                "result": None,
                "message": f"Помилка відкриття: {str(e)}"
            }
