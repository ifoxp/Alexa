import webbrowser
import urllib.request
import urllib.parse
import re
from typing import Dict, Any
from .base_plugin import SmartPlugin


class BrowserSearchPlugin(SmartPlugin):
    """Плагін для пошуку в браузері: Google, YouTube (пошук або пряме відтворення першого відео)."""

    @property
    def name(self) -> str:
        return "browser_search"

    @property
    def description(self) -> str:
        return "Пошук в інтернеті. Вміє гуглити, шукати відео на YouTube, а також одразу вмикати потрібне відео (навіть якщо назва приблизна).(не для новин)"

    @property
    def commands(self) -> Dict[str, str]:
        return {
            "search_google": "Загальний пошук в інтернеті (Google) для будь-яких питань чи інформації",
            "search_youtube": "Просто відкрити пошук на YouTube за запитом (коли користувач хоче щось подивитися але не каже що саме)",
            "play_youtube_video": "Знайти і ОДРАЗУ ВІДКРИТИ (відтворити) перше відео на YouTube за запитом (наприклад: 'останнє відео Джо Спіна', 'тучний жаб'(користувач може казати подібні назви типу Joss PIN, ми маєш шукати на українськумо або російському ютубі те що хоче отримати користувач))"
        }

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        """Виконує команду плагіна."""
        try:
            print(f"\n=== BROWSER_SEARCH DEBUG ===")
            print(f"[1] Received command: {command_name}")
            print(f"[2] All kwargs: {kwargs}")

            # Отримуємо запит (value або query)
            query = kwargs.get("value") or kwargs.get("query") or kwargs.get("video", "")

            if not query:
                return {"success": False, "result": None, "message": "Запит не може бути пустим"}

            if command_name == "search_google":
                return await self._search_google(query)

            elif command_name == "search_youtube":
                return await self._search_youtube(query)

            elif command_name == "play_youtube_video":
                return await self._play_youtube_video(query)

            else:
                return {"success": False, "result": None, "message": f"Невідома команда: {command_name}"}

        except Exception as e:
            print(f"[ERROR] Error executing {command_name} | {e}")
            return {"success": False, "result": None, "message": f"Помилка виконання: {str(e)}"}

    async def _search_google(self, query: str) -> Dict[str, Any]:
        """Простий пошук в Google."""
        try:
            search_query = urllib.parse.quote(query)
            google_url = f"https://www.google.com/search?q={search_query}"
            
            webbrowser.open(google_url)
            print(f"[INFO] Opened Google search: {query}")
            
            return {
                "success": True, 
                "result": {"url": google_url}, 
                "message": f"Відкриваю пошук в Google за запитом: {query}"
            }
        except Exception as e:
            return {"success": False, "result": None, "message": str(e)}

    async def _search_youtube(self, query: str) -> Dict[str, Any]:
        """Відкриває сторінку з результатами пошуку на YouTube."""
        try:
            search_query = urllib.parse.quote(query)
            youtube_url = f"https://www.youtube.com/results?search_query={search_query}"
            
            webbrowser.open(youtube_url)
            print(f"[INFO] Opened YouTube search: {query}")
            
            return {
                "success": True, 
                "result": {"url": youtube_url}, 
                "message": f"Шукаю '{query}' на YouTube."
            }
        except Exception as e:
            return {"success": False, "result": None, "message": str(e)}

    async def _play_youtube_video(self, query: str) -> Dict[str, Any]:
        """Непомітно шукає відео, знаходить перше посилання і відкриває саме його."""
        try:
            print(f"[YT PLAYER] Спроба знайти пряме посилання для: '{query}'")
            
            # Формуємо запит
            search_query = urllib.parse.quote(query)
            search_url = f"https://www.youtube.com/results?search_query={search_query}"
            
            # Робимо прихований запит до YouTube (прикидаємося браузером)
            req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            html_content = urllib.request.urlopen(req).read().decode('utf-8')
            
            # Шукаємо всі ID відео за допомогою регулярного виразу
            video_ids = re.findall(r"watch\?v=(\S{11})", html_content)
            
            if video_ids:
                # Беремо перше знайдене відео
                first_video_id = video_ids[0]
                video_url = f"https://www.youtube.com/watch?v={first_video_id}"
                
                print(f"[YT PLAYER] Знайдено відео: {video_url}")
                webbrowser.open(video_url)
                
                return {
                    "success": True, 
                    "result": {"url": video_url}, 
                    "message": f"Вмикаю відео за запитом: {query}"
                }
            else:
                # Якщо регулярка не спрацювала (наприклад, ютуб змінив дизайн), 
                # то просто відкриваємо пошук (fallback)
                print("[YT PLAYER] Відео не знайдено, відкриваю звичайний пошук.")
                webbrowser.open(search_url)
                return {
                    "success": True, 
                    "result": {"url": search_url}, 
                    "message": f"Відкриваю результати пошуку для: {query}"
                }
                
        except Exception as e:
            print(f"[ERROR] Failed to play YouTube video: {query} | {e}")
            return {"success": False, "result": None, "message": f"Помилка відтворення: {str(e)}"}