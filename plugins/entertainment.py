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
        return "Розваги. Генерує унікальні, нешаблонні жарти та цікаві факти. Завжди використовуй цей плагін для команд 'розкажи жарт' або 'цікавий факт'."

    @property
    def commands(self) -> Dict[str, str]:
        # Спростили команди: тепер все йде через генерацію
        return {
            "tell_joke": "Розказати жарт (можна вказати тему)",
            "tell_fact": "Розказати цікавий факт (можна вказати тему)",
            "tell_random": "Розказати щось випадкове (жарт або факт)"
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

            elif command_name == "tell_random":
                if random.choice([True, False]):
                    return await self._generate_joke(topic)
                else:
                    return await self._generate_fact(topic)
            else:
                return {"success": False, "result": None, "message": f"Невідома команда: {command_name}"}

        except Exception as e:
            self.log_error(f"Error executing {command_name}", error=str(e))
            return {"success": False, "result": None, "message": f"Помилка виконання команди: {str(e)}"}

    def _get_random_topic(self, is_joke: bool) -> str:
        """Підкидає цікаві теми, якщо користувач не задав свою, щоб уникати повторень."""
        if is_joke:
            topics = ["програмування", "штучний інтелект", "відеоігри", "баги в коді", "лінощі", "Python або C#", "ПК геймінг"]
        else:
            topics = ["космос", "наукові відкриття", "кіберпанк", "історію технологій", "загадки природи", "комп'ютерне залізо", "психологію"]
        return random.choice(topics)

    async def _generate_joke(self, topic: str = "") -> Dict[str, Any]:
        """Генерує новий, унікальний жарт через GPT, адаптований для TTS."""
        if not smart_ai.smart_assistant:
            joke = random.choice(self.fallback_jokes)
            return {"success": True, "result": {"joke": joke}, "message": "Розказую жарт", "speak_text": joke}

        actual_topic = topic if topic else self._get_random_topic(is_joke=True)

        try:
            prompt = f"""Ти - крутий стендап-комік. Розкажи ОДИН свіжий, нешаблонний жарт на тему: "{actual_topic}".

КРИТИЧНІ ПРАВИЛА ДЛЯ ОЗВУЧКИ:
1. Текст буде читати робот. Щоб це звучало як справжній жарт, а не скоромовка, ОБОВ'ЯЗКОВО використовуй трикрапки (...) перед панчлайном (кульмінацією).
2. Роби речення короткими. Використовуй знаки питання та оклику для емоцій.
3. Жодних банальних жартів з інтернету. Придумай щось дотепне і сучасне.
4. Тільки українською мовою. Без вступних слів (одразу жарт).

ФОРМАТ: Тільки текст жарту з паузами (...)."""

            response = await smart_ai.smart_assistant.client.chat.completions.create(
                model=smart_ai.smart_assistant.model,
                messages=[
                    {"role": "system", "content": "Ти комік з чудовим почуттям гумору та таймінгом."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.9 # Висока температура для креативності
            )

            generated_joke = response.choices[0].message.content.strip()

            return {
                "success": True,
                "result": {"joke": generated_joke, "topic": actual_topic},
                "message": f"Жарт на тему: {actual_topic}",
                "speak_text": generated_joke
            }

        except Exception as e:
            self.log_error(f"Failed to generate joke: {e}")
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

            response = await smart_ai.smart_assistant.client.chat.completions.create(
                model=smart_ai.smart_assistant.model,
                messages=[
                    {"role": "system", "content": "Ти ерудит, який вміє зацікавити слухача з перших секунд."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.8
            )

            generated_fact = response.choices[0].message.content.strip()

            return {
                "success": True,
                "result": {"fact": generated_fact, "topic": actual_topic},
                "message": f"Цікавий факт: {actual_topic}",
                "speak_text": generated_fact
            }

        except Exception as e:
            self.log_error(f"Failed to generate fact: {e}")
            fact = random.choice(self.fallback_facts)
            return {"success": True, "result": {"fact": fact}, "message": "Розказую факт", "speak_text": fact}