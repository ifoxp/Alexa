# browser_search.py
import webbrowser
from typing import Dict, Any
from .base_plugin import SmartPlugin


class BrowserSearchPlugin(SmartPlugin):
    """Плагін для пошуку в браузері, YouTube та інших веб-сервісах."""

    @property
    def name(self) -> str:
        return "browser_search"

    @property
    def description(self) -> str:
        return "Пошук в Google, YouTube, відкриття веб-сайтів. Підтримує пошук відео, каналів, загальний пошук в інтернеті."

    @property
    def commands(self) -> Dict[str, str]:
        return {
            "search_youtube": "знайти відео на YouTube за запитом",
            "search_google": "пошук в Google за запитом, включаючи пошук контенту на конкретних сайтах",
            "open_website": "відкрити веб-сайт за прямим URL (тільки для готових посилань типу google.com)",
            "search_youtube_channel": "знайти канал на YouTube"
        }

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        """Виконує команду плагіна."""
        try:
            print(f"\n=== BROWSER_SEARCH DEBUG ===")
            print(f"[1] Received command: {command_name}")
            print(f"[2] All kwargs: {kwargs}")

            if command_name == "search_youtube":
                query = kwargs.get("value") or kwargs.get("query", "")
                print(f"[3] search_youtube with query: '{query}'")
                result = await self._search_youtube(query)
                print(f"[RESULT] search_youtube result: {result}")
                return result

            elif command_name == "search_google":
                query = kwargs.get("value") or kwargs.get("query", "")
                print(f"[3] search_google with query: '{query}'")
                result = await self._search_google(query)
                print(f"[RESULT] search_google result: {result}")
                return result

            elif command_name == "open_website":
                url = kwargs.get("value") or kwargs.get("url", "")
                print(f"[3] open_website with url: '{url}'")
                result = await self._open_website(url)
                print(f"[RESULT] open_website result: {result}")
                return result

            elif command_name == "search_youtube_channel":
                channel = kwargs.get("value") or kwargs.get("channel", "")
                print(f"[3] search_youtube_channel with channel: '{channel}'")
                result = await self._search_youtube_channel(channel)
                print(f"[RESULT] search_youtube_channel result: {result}")
                return result

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

    async def _search_youtube(self, query: str) -> Dict[str, Any]:
        """Пошук відео на YouTube."""
        if not query:
            return {
                "success": False,
                "result": None,
                "message": "Запит для пошуку не може бути пустим"
            }

        try:
            # Формуємо URL для YouTube пошуку
            search_query = query.replace(" ", "+")
            youtube_url = f"https://www.youtube.com/results?search_query={search_query}"

            webbrowser.open(youtube_url)
            self.log_info(f"Opened YouTube search: {query}")

            return {
                "success": True,
                "result": {"url": youtube_url, "query": query},
                "message": f"Відкрито пошук на YouTube: {query}"
            }

        except Exception as e:
            self.log_error(f"Failed to search YouTube: {query}", error=str(e))
            return {
                "success": False,
                "result": None,
                "message": f"Помилка пошуку на YouTube: {str(e)}"
            }

    async def _search_google(self, query: str) -> Dict[str, Any]:
        """Пошук в Google."""
        if not query:
            return {
                "success": False,
                "result": None,
                "message": "Запит для пошуку не може бути пустим"
            }

        try:
            # Очищуємо запит від site: параметрів що можуть зламати посилання
            clean_query = query
            if "site:" in clean_query:
                # Видаляємо всі site: параметри
                import re
                clean_query = re.sub(r'\s*site:[^\s]+', '', clean_query).strip()
                print(f"[CLEAN] Removed site: parameter from '{query}' -> '{clean_query}'")

            # Формуємо URL для Google пошуку
            search_query = clean_query.replace(" ", "+")
            google_url = f"https://www.google.com/search?q={search_query}"

            webbrowser.open(google_url)
            self.log_info(f"Opened Google search: {clean_query}")

            return {
                "success": True,
                "result": {"url": google_url, "query": clean_query},
                "message": f"Відкрито пошук в Google: {clean_query}"
            }

        except Exception as e:
            self.log_error(f"Failed to search Google: {query}", error=str(e))
            return {
                "success": False,
                "result": None,
                "message": f"Помилка пошуку в Google: {str(e)}"
            }

    async def _open_website(self, url: str) -> Dict[str, Any]:
        """Відкриває веб-сайт."""
        if not url:
            return {
                "success": False,
                "result": None,
                "message": "URL не може бути пустим"
            }

        try:
            # Якщо це схоже на URL - відкриваємо як сайт
            if url.startswith(('http://', 'https://')) or ('.' in url and ' ' not in url):
                # Це справжній URL
                if not url.startswith(('http://', 'https://')):
                    url = f"https://{url}"
            else:
                # Це пошуковий запит - робимо Google пошук
                print(f"[WEBSITE] Treating '{url}' as search query, redirecting to Google")
                return await self._search_google(url)

            webbrowser.open(url)
            self.log_info(f"Opened website: {url}")

            return {
                "success": True,
                "result": {"url": url},
                "message": f"Відкрито веб-сайт: {url}"
            }

        except Exception as e:
            self.log_error(f"Failed to open website: {url}", error=str(e))
            return {
                "success": False,
                "result": None,
                "message": f"Помилка відкриття веб-сайту: {str(e)}"
            }

    async def _search_youtube_channel(self, channel: str) -> Dict[str, Any]:
        """Пошук каналу на YouTube."""
        if not channel:
            return {
                "success": False,
                "result": None,
                "message": "Назва каналу не може бути пустою"
            }

        try:
            # Формуємо URL для пошуку каналу на YouTube
            search_query = f"{channel} channel".replace(" ", "+")
            youtube_url = f"https://www.youtube.com/results?search_query={search_query}&sp=EgIQAg%253D%253D"

            webbrowser.open(youtube_url)
            self.log_info(f"Opened YouTube channel search: {channel}")

            return {
                "success": True,
                "result": {"url": youtube_url, "channel": channel},
                "message": f"Відкрито пошук каналу на YouTube: {channel}"
            }

        except Exception as e:
            self.log_error(f"Failed to search YouTube channel: {channel}", error=str(e))
            return {
                "success": False,
                "result": None,
                "message": f"Помилка пошуку каналу: {str(e)}"
            }