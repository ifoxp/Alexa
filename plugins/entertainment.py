import random
from typing import Dict, Any
from .base_plugin import SmartPlugin
import smart_ai

class EntertainmentPlugin(SmartPlugin):
    """Плагін для розваг - унікальні жарти та вражаючі факти з правильною інтонацією для озвучки."""

    def __init__(self):
        super().__init__()
        # Запасна база, якщо відпаде API
        self.fallback_jokes = [
            "Чому програмісти не люблять природу? ... Там забагато багів!",
            "Що робить програміст, коли не може заснути? ... Рахує овець. В двійковій системі."
        ]
        self.fallback_facts = [
            "В Україні знаходиться найглибша станція метро у світі — 'Арсенальна'. Її глибина... 105 метрів.",
            "Український алфавіт має 33 літери і є одним з найбагатших за кількістю звуків."
        ]

    @property
    def name(self) -> str:
        return "entertainment"

    @property
    def description(self) -> str:
        return "Розваги і гумор. ТІЛЬКИ для жартів та фактів. Використовуй цей плагін ЛИШЕ для команд: 'розкажи жарт', 'цікавий факт', 'розсміши мене'. НЕ використовуй для музики, програм або інших дій."

    @property
    def commands(self) -> Dict[str, str]:
        return {
            "tell_joke": "Розкажи жарт (можна вказати тему)",
            "tell_fact": "Розкажи цікавий факт (можна вказати тему)"
        }

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        """Виконує команду плагіна."""
        try:
            print(f"\n=== ENTERTAINMENT DEBUG ===")
            print(f"[1] Received command: {command_name}")
            print(f"[2] All kwargs: {kwargs}")

            topic = kwargs.get("value") or kwargs.get("topic", "")

            if command_name == "tell_joke":
                return await self._generate_joke(topic)

            elif command_name == "tell_fact":
                return await self._generate_fact(topic)

            else:
                return {"success": False, "result": None, "message": f"Невідома команда: {command_name}"}

        except Exception as e:
            print(f"[ERROR] Error executing {command_name} | {e}")
            return {"success": False, "result": None, "message": f"Помилка виконання команди: {str(e)}"}

    def _get_random_topic(self, is_joke: bool) -> str:
        """Підкидає цікаві теми, якщо користувач не задав свою, щоб уникати повторень."""
        if is_joke:
            topics = ["баги в програмуванні", "коти і клавіатури", "біль геймерів", "VR і реальність", "дедлайни", "моди на ігри типу Terraria", "ціни на відеокарти"]
        else:
            topics = ["майбутнє штучного інтелекту", "кібернетика та андроїди", "новітні технології відеокарт", "космос", "як працює пам'ять", "історія створення популярних ігор"]
        return random.choice(topics)

    async def _generate_joke(self, topic: str = "") -> Dict[str, Any]:
        """Генерує новий, унікальний жарт через GPT, адаптований для TTS."""
        if not smart_ai.smart_assistant:
            joke = random.choice(self.fallback_jokes)
            return {"success": True, "result": {"joke": joke}, "message": "Розказую жарт", "speak_text": joke}

        actual_topic = topic if topic else self._get_random_topic(is_joke=True)

        try:
            # ОНОВЛЕНИЙ ПРОМТ ДЛЯ ЖАРТІВ
            prompt = f"""Ти — саркастичний і трохи цинічний гік. Напиши ОДИН дуже короткий жарт або іронічне спостереження на тему: "{actual_topic}".

КРИТИЧНІ ПРАВИЛА:
1. ЖОДНИХ класичних анекдотів, ніяких "зустрічаються якось...".
2. Жартуй через іронію, абсурд або життєвий біль. Жарт має бути неочікуваним і сучасним.
3. Текст читатиме робот. Став трикрапки (...) перед панчлайном (кульмінацією) для паузи.
4. Максимум 1-3 речення. Тільки українською мовою. Без вступів.

Приклад вайбу: "Купив потужну відеокарту, щоб працювати швидше... Тепер ігри завантажуються так швидко, що я не встигаю читати підказки на екрані."
"""

            generated_joke = await self.ask_gpt(prompt, max_tokens=250, temperature=0.9)

            return {
                "success": True,
                "result": {"joke": generated_joke, "topic": actual_topic},
                "message": f"Жарт на тему: {actual_topic}",
                "speak_text": generated_joke
            }

        except Exception as e:
            print(f"[ERROR] Failed to generate joke: {e}")
            joke = random.choice(self.fallback_jokes)
            return {"success": True, "result": {"joke": joke}, "message": "Розказую жарт", "speak_text": joke}

    async def _generate_fact(self, topic: str = "") -> Dict[str, Any]:
        """Генерує глибокий, маловідомий факт через GPT, адаптований для TTS."""
        if not smart_ai.smart_assistant:
            fact = random.choice(self.fallback_facts)
            return {"success": True, "result": {"fact": fact}, "message": "Розказую факт", "speak_text": fact}

        actual_topic = topic if topic else self._get_random_topic(is_joke=False)

        try:
            prompt = f"""Ти - харизматичний ведучий науково-популярного шоу. Розкажи ОДИН вражаючий, маловідомий факт на тему: "{actual_topic}".

КРИТИЧНІ ПРАВИЛА ДЛЯ ОЗВУЧКИ:
1. Текст буде читати робот. Розбивай текст на короткі речення.
2. Використовуй коми та трикрапки (...), щоб створити інтригу і змусити синтезатор робити природні паузи.
3. Уникай сухих цифр і енциклопедичного тону. Розкажи це як захопливу міні-історію.
4. Тільки українською мовою. Максимум 3-4 речення.

ФОРМАТ: Тільки текст факту з паузами."""

            generated_fact = await self.ask_gpt(prompt, max_tokens=300, temperature=0.8)

            return {
                "success": True,
                "result": {"fact": generated_fact, "topic": actual_topic},
                "message": f"Цікавий факт: {actual_topic}",
                "speak_text": generated_fact
            }

        except Exception as e:
            print(f"[ERROR] Failed to generate fact: {e}")
            fact = random.choice(self.fallback_facts)
            return {"success": True, "result": {"fact": fact}, "message": "Розказую факт", "speak_text": fact}