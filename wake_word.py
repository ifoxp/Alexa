import datetime
import time

class WakeWordHandler:
    def __init__(self):
        self.last_detection_time = 0
        self.detection_cooldown = 1.0  # Секунди між детекціями

    def on_wake_word_detected(self, wake_word, confidence):
        """
        Обробка виявленого wake word

        Args:
            wake_word (str): Назва виявленого wake word
            confidence (float): Рівень впевненості (0.0 - 1.0)
        """
        current_time = time.time()

        # Перевірка на cooldown щоб уникнути повторних спрацювань
        if current_time - self.last_detection_time < self.detection_cooldown:
            return

        self.last_detection_time = current_time

        # Форматування часу
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")

        # Виведення повідомлення про розпізнавання
        print(f"\n🔥 [{timestamp}] WAKE WORD РОЗПІЗНАНО!   Впевненість: {confidence:.2%}")

        # Додаткові дії можна додати тут
        self._perform_wake_actions(wake_word, confidence)

    def _perform_wake_actions(self, wake_word, confidence):
        """
        Додаткові дії після розпізнавання wake word
        """
        # Тут можна додати додаткову логіку
        # Наприклад: запуск асистента, відправка сигналу тощо
        pass

    def set_cooldown(self, seconds):
        """
        Встановлення часу cooldown між детекціями

        Args:
            seconds (float): Час в секундах
        """
        self.detection_cooldown = seconds