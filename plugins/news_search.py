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
        return "Пошук новин в інтернеті. Збирає актуальні новини з інтернету та розповідає їх голосом. Використовуй для команд на зразок 'розкажи новини', 'що у світі', 'новини технологій'."

    @property
    def commands(self) -> Dict[str, str]:
        return {
            "read_ukraine_news": "Розкажи головні новини України",
            "read_world_news": "Розкажи світові новини",
            "read_tech_news": "Розкажи новини технологій та IT",
            "read_sports_news": "Розкажи спортивні новини",
            "read_news_topic": "Розкажи новини на конкретну тему (наприклад: новини про ШІ, економіку тощо)"
        }

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        """Виконує команду плагіна."""
        try:
            print(f"\n=== NEWS_READER DEBUG ===")
            print(f"[1] Received command: {command_name}")

            if command_name == "read_ukraine_news":
                return await self._read_news("Україна", "українських новин")
            
            elif command_name == "read_world_news":
                return await self._read_news("Світ", "світових новин")
            
            elif command_name == "read_tech_news":
                return await self._read_news("Технології IT", "сфери технологій")
            
            elif command_name == "read_sports_news":
                return await self._read_news("Спорт", "спорту")
            
            elif command_name == "read_news_topic":
                topic = kwargs.get("value") or kwargs.get("topic", "головні події")
                return await self._read_news(topic, f"теми '{topic}'")
            
            else:
                return {"success": False, "result": None, "message": f"Невідома команда: {command_name}"}

        except Exception as e:
            self.log_error(f"Error executing {command_name}", error=str(e))
            return {"success": False, "result": None, "message": f"Помилка виконання: {str(e)}"}

    async def _fetch_real_headlines(self, topic: str, limit: int = 5) -> str:
        """Парсить реальні свіжі заголовки через Google News RSS."""
        try:
            print(f"[NEWS FETCH] Збираю свіжі заголовки для: {topic}...")
            encoded_topic = urllib.parse.quote(topic)
            # URL для пошуку новин українською
            url = f"https://news.google.com/rss/search?q={encoded_topic}&hl=uk&gl=UA&ceid=UA:uk"
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            response = urllib.request.urlopen(req)
            xml_data = response.read()
            
            root = ET.fromstring(xml_data)
            headlines = []
            
            # Дістаємо вказану кількість новин
            for item in root.findall('./channel/item')[:limit]:
                title = item.find('title').text
                # Відрізаємо назву видання в кінці заголовка (вона йде після " - ")
                clean_title = title.rsplit(' - ', 1)[0]
                headlines.append(f"- {clean_title}")
                
            if not headlines:
                return ""
            
            return "\n".join(headlines)
        except Exception as e:
            self.log_error("Failed to fetch RSS", error=str(e))
            return ""

    async def _read_news(self, search_query: str, topic_name: str) -> Dict[str, Any]:
        """Універсальний метод: бере заголовки і просить GPT зробити гарну розповідь."""
        
        # 1. Дістаємо справжні новини
        headlines = await self._fetch_real_headlines(search_query, limit=4)
        
        if not headlines:
            message = f"Вибачте, сер, але я не зміг знайти свіжих новин для {topic_name}."
            return {"success": False, "result": None, "message": message, "speak_text": message}

        # 2. Якщо ШІ підключений, даємо йому красиво це прочитати
        if smart_ai.smart_assistant:
            try:
                prompt = f"""Ти - голосовий асистент Jarvis. Розкажи користувачу новини.
Ось 4 найсвіжіші реальні заголовки ({topic_name}):
{headlines}

ПРАВИЛА:
1. Зроби з цих заголовків природну, зв'язну розповідь.
2. Не читай їх як нудний список з тире. Об'єднай їх у цікавий випуск новин.
3. Мова: українська.
4. Обсяг: 3-4 речення.
5. Закінчи розповідь ввічливо, використовуючи звертання "сер".

ФОРМАТ:
Сьогодні у {topic_name}: [твій цікавий переказ]."""

                response = await smart_ai.smart_assistant.client.chat.completions.create(
                    model=smart_ai.smart_assistant.model,
                    messages=[
                        {"role": "system", "content": "Ти диктор та асистент Jarvis. Говориш чітко, природно та цікаво."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=250,
                    temperature=0.7
                )
                
                final_text = response.choices[0].message.content.strip()
                
            except Exception as e:
                self.log_error("GPT formatting failed", error=str(e))
                # Запасний варіант, якщо GPT відпав
                final_text = f"Ось останні новини, сер. {headlines.replace('- ', '')}"
        else:
            final_text = f"Ось останні новини, сер. {headlines.replace('- ', '')}"

        print(f"[NEWS RESULT] Згенерований текст: {final_text}")

        return {
            "success": True,
            "result": {"topic": topic_name, "raw_headlines": headlines},
            "message": f"Озвучую новини: {topic_name}",
            "speak_text": final_text
        }