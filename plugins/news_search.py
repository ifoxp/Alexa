import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import asyncio
from typing import Dict, Any
from .base_plugin import SmartPlugin
import smart_ai

class NewsReaderPlugin(SmartPlugin):
    """Плагін для справжнього читання новин: збирає свіжі заголовки і озвучує їх через GPT."""

    @property
    def name(self) -> str:
        return "news_search"

    @property
    def description(self) -> str:
        return "Збирає актуальні новини з інтернету та розповідає їх голосом. Використовуй для будь-яких запитів про новини, події у світі, спорт, технології тощо."

    @property
    def commands(self) -> Dict[str, str]:
        return {
            "read_news": "Прочитати новини. Тему новин (Україна, технології, спорт, ШІ тощо) передавай у параметр 'value'. Якщо користувач не вказав тему або сказав 'головні/свіжі', передай 'головні'."
        }

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        """Виконує команду плагіна."""
        try:
            print(f"[NEWS] execute: command={command_name}, kwargs={kwargs}")

            if command_name == "read_news":
                # Витягуємо тему. Якщо ШІ нічого не дав, ставимо "головні"
                topic = kwargs.get("value") or kwargs.get("topic", "головні")
                print(f"[NEWS] topic resolved to: '{topic}'")
                return await self._read_news(topic)

            else:
                print(f"[NEWS] unknown command: {command_name}")
                return {"success": False, "result": None, "message": f"Невідома команда: {command_name}"}

        except Exception as e:
            print(f"[NEWS] error in execute_command: {e}")
            return {"success": False, "result": None, "message": f"Помилка виконання: {str(e)}"}

    async def _fetch_real_headlines(self, topic: str, limit: int = 5) -> str:
        """Парсить реальні свіжі заголовки через Google News RSS."""
        try:
            print(f"[NEWS] fetching RSS headlines for topic='{topic}', limit={limit}")

            # Якщо користувач просто хоче новини, беремо головну стрічку без пошуку
            if topic.lower() in ["головні", "загальні", "все", "світ", "новини"]:
                url = "https://news.google.com/rss?hl=uk&gl=UA&ceid=UA:uk"
            else:
                # Якщо є конкретна тема, робимо пошук
                encoded_topic = urllib.parse.quote(topic)
                url = f"https://news.google.com/rss/search?q={encoded_topic}&hl=uk&gl=UA&ceid=UA:uk"

            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req)
            xml_data = response.read()

            root = ET.fromstring(xml_data)
            headlines = []

            for item in root.findall('./channel/item')[:limit]:
                title = item.find('title').text
                clean_title = title.rsplit(' - ', 1)[0]
                headlines.append(f"- {clean_title}")

            print(f"[NEWS] fetched {len(headlines)} headlines for topic='{topic}'")
            for h in headlines:
                print(f"[NEWS]   {h}")

            return "\n".join(headlines) if headlines else ""
        except Exception as e:
            print(f"[NEWS] RSS fetch failed: {e}")
            return ""

    async def _read_news(self, topic: str) -> Dict[str, Any]:
        """Універсальний метод: бере заголовки і просить GPT зробити гарну розповідь."""

        # Беремо 7 заголовків, щоб ШІ мав з чого вибрати
        headlines = await self._fetch_real_headlines(topic, limit=7)

        if not headlines:
            message = f"Вибачте, сер, але я не зміг знайти свіжих новин на тему '{topic}'."
            print(f"[NEWS] no headlines found for topic='{topic}', returning failure")
            return {"success": False, "result": None, "message": message, "speak_text": message}

        if smart_ai.smart_assistant:
            try:
                prompt = f"""Ти — JARVIS, особистий британський асистент. Твоє завдання — провести короткий брифінг новин.

ТЕМА ЗАПИТУ: {topic}
СВІЖІ ЗАГОЛОВКИ:
{headlines}

ЯК ФОРМУВАТИ РОЗПОВІДЬ:
1. Обери 2-3 найважливіші новини зі списку. НЕ ВИГАДУЙ НІЧОГО СВОГО! Озвучуй тільки те, що є в заголовках.
2. Зроби плавні переходи (наприклад: "Тим часом...", "Також варто відзначити...").
3. Використовуй трикрапки (...) для пауз перед важливими словами.
4. Тон: спокійний, професійний.
5. Завжди починай зі звертання "Сер".

ФОРМАТ: Тільки текст для озвучки українською мовою."""

                print(f"[NEWS] sending prompt to GPT (first 80 chars): '{prompt[:80].strip()}'")
                final_text = await self.ask_gpt(prompt, max_tokens=300, temperature=0.5)
                print(f"[NEWS] GPT generated speak_text: '{final_text}'")

            except Exception as e:
                print(f"[NEWS] GPT formatting failed: {e}, using raw headlines as fallback")
                final_text = f"Ось останні новини, сер. {headlines.replace('- ', '')}"
        else:
            print(f"[NEWS] GPT unavailable, using raw headlines directly")
            final_text = f"Ось останні новини, сер. {headlines.replace('- ', '')}"

        return {
            "success": True,
            "result": {"topic": topic, "raw_headlines": headlines},
            "message": f"Озвучую новини: {topic}",
            "speak_text": final_text
        }
