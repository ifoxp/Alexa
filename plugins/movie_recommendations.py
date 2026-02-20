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
            print(f"\n=== MOVIE_RECOMMENDATIONS DEBUG ===")
            print(f"[1] Received command: {command_name}")
            print(f"[2] All kwargs: {kwargs}")

            if command_name == "recommend_movie":
                # Отримуємо запит, жанр або настрій
                genre_or_mood = kwargs.get("value") or kwargs.get("genre") or kwargs.get("mood", "на твій смак")
                return await self._recommend_movie(genre_or_mood)

            elif command_name == "search_movie":
                movie_name = kwargs.get("value") or kwargs.get("movie", "")
                return await self._search_movie(movie_name)

            else:
                return {
                    "success": False,
                    "result": None,
                    "message": f"Невідома команда: {command_name}"
                }

        except Exception as e:
            self.log_error(f"Error executing {command_name}", error=str(e))
            return {
                "success": False,
                "result": None,
                "message": f"Помилка виконання команди: {str(e)}"
            }

    async def _recommend_movie(self, request_text: str) -> Dict[str, Any]:
        """Запитує GPT про рекомендацію, парсить назву та відкриває пошук."""
        if not smart_ai.smart_assistant:
            # Якщо GPT відключений, просто шукаємо як звичайний текст
            return await self._search_movie(request_text)

        try:
            # Змушуємо GPT думати і повертати інформацію у строгому форматі
            prompt = f"""Ти - кінокритик і голосовий асистент Jarvis.
Користувач просить порадити щось подивитися. Запит: "{request_text}".
Якщо запит загальний, можеш порадити якісний екшн, цікаве аніме (в стилі Сім смертних гріхів) або щось з цікавою мультиплікацією/гумором (в стилі Хазбін Готель).

ОБОВ'ЯЗКОВИЙ ФОРМАТ ВІДПОВІДІ (строго 2 рядки):
Назва: [Тільки точна назва фільму/серіалу/аніме українською або англійською]
Опис: [2-3 речення про те, чому це круто і варто уваги. Без банальних фраз "Я рекомендую". Природна розповідь, що інтригує. В кінці додай "сер".]"""

            response = await smart_ai.smart_assistant.client.chat.completions.create(
                model=smart_ai.smart_assistant.model,
                messages=[
                    {"role": "system", "content": "Ти креативний асистент, який розуміється на кіно і дає круті поради."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.8
            )

            gpt_reply = response.choices[0].message.content.strip()
            print(f"[MOVIE_REC] GPT Reply:\n{gpt_reply}")

            # Витягуємо назву та опис із відповіді GPT
            title = ""
            description = ""
            for line in gpt_reply.split('\n'):
                if line.startswith("Назва:"):
                    title = line.replace("Назва:", "").strip()
                elif line.startswith("Опис:"):
                    description = line.replace("Опис:", "").strip()

            # Якщо GPT чомусь збився з формату, рятуємо ситуацію
            if not title or not description:
                title = request_text if request_text != "на твій смак" else "Щось цікаве"
                description = gpt_reply if gpt_reply else "Ось що я знайшов, сер."

            # Відкриваємо пошук на uakino
            return await self._search_and_open_uakino(title, description)

        except Exception as e:
            self.log_error("GPT recommendation failed", error=str(e))
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
            self.log_info(f"Opened uakino search for: {movie_name}")
            
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
            self.log_error(f"Failed to search movie on uakino: {movie_name}", error=str(e))
            return {
                "success": False,
                "result": None,
                "message": f"Помилка відкриття: {str(e)}"
            }