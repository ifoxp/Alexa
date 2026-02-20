import speech_recognition as sr
import settings
import asyncio
import concurrent.futures
import threading
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from logger_config import get_logger

logger = get_logger('transcriber')

class OnlineTranscriber:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone(
            sample_rate=settings.RATE,
            chunk_size=settings.CHUNK
        )
        # Multi-language support
        self.languages = ["uk-UA", "ru-RU", "en-US"]
        self.current_language_index = 0
        self.current_language = self.languages[0]
        
        # Початкове калібрування з покращеними налаштуваннями
        with self.microphone as source:
            logger.info("Starting microphone calibration")
            self.recognizer.adjust_for_ambient_noise(source, duration=2.0)
            
            # Вмикаємо динамічний поріг, щоб він підлаштовувався під шум кулерів/вулиці
            self.recognizer.dynamic_energy_threshold = True
            
            # Зменшуємо базовий поріг, щоб краще чути тихий голос
            self.recognizer.energy_threshold = 250 
            
            # Збільшуємо час паузи, щоб ти міг робити перерви між словами
            self.recognizer.pause_threshold = 2.0  
            self.recognizer.phrase_threshold = 0.1 
            self.recognizer.non_speaking_duration = 0.5
            logger.info("Microphone calibration completed with optimized settings")

    def set_language(self, lang_code):
        """Встановлює конкретну мову."""
        if lang_code in self.languages:
            self.current_language = lang_code
            self.current_language_index = self.languages.index(lang_code)
            logger.info("Language changed", extra={'language': lang_code})
        else:
            logger.warning("Unsupported language", extra={'requested': lang_code, 'supported': self.languages})

    def cycle_language(self):
        """Переключає на наступну мову в циклі."""
        self.current_language_index = (self.current_language_index + 1) % len(self.languages)
        self.current_language = self.languages[self.current_language_index]
        logger.info("Language cycled", extra={
            'new_language': self.current_language,
            'index': self.current_language_index
        })
        return self.current_language

    async def recognize_multilang(self, audio):
        """Спробує розпізнати текст на всіх підтримуваних мовах."""
        results = {}

        for lang in self.languages:
            try:
                old_lang = self.current_language
                self.current_language = lang
                result = self._recognize_with_retry(audio)
                self.current_language = old_lang  # Відновлюємо

                if result:
                    results[lang] = result
                    logger.debug("Multi-lang recognition success", extra={
                        'language': lang,
                        'transcript': result
                    })
            except Exception as e:
                logger.debug("Multi-lang recognition failed", extra={
                    'language': lang,
                    'error': str(e)
                })
                continue

        # Повертаємо найкращий результат (найдовший текст)
        if results:
            best_lang = max(results.keys(), key=lambda k: len(results[k]))
            logger.info("Multi-lang recognition completed", extra={
                'detected_language': best_lang,
                'transcript': results[best_lang],
                'all_results': results
            })
            return results[best_lang], best_lang

        return None, None

    def listen_and_transcribe(self, timeout):
        """Слухає одну фразу з динамічним таймаутом."""
        if not timeout or timeout <= 0:
            return None

        with self.microphone as source:
          
            try:
                print(f" M... (очікую до {timeout:.1f}с)")
                # Додаємо phrase_time_limit для захоплення довших фраз
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=10  # Максимум 10 секунд на фразу
                )
            except sr.WaitTimeoutError:
                return None

        return self._recognize_with_retry(audio)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        retry=retry_if_exception_type(sr.RequestError),
        reraise=True
    )
    def _recognize_with_retry(self, audio):
        """Розпізнавання з retry механізмом."""
        try:
            transcript = self.recognizer.recognize_google(
                audio,
                language=self.current_language
            )
            logger.debug("Speech recognition successful", extra={
                'transcript': transcript,
                'language': self.current_language
            })
            return transcript
        except sr.UnknownValueError:
            # Не можемо розпізнати - не retry
            logger.debug("Speech not recognized")
            return None
        except sr.RequestError as e:
            logger.warning("Speech recognition request failed", extra={
                'error': str(e),
                'language': self.current_language,
                'retry': True
            })
            raise  # Retry спрацює

    async def listen_and_transcribe_async(self, timeout):
        """Async версія слухання з можливістю скасування."""
        if not timeout or timeout <= 0:
            return None

        loop = asyncio.get_event_loop()

        try:
            # Виконуємо блокуючу операцію в окремому потоці
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self.listen_and_transcribe, timeout)
                # Чекаємо результат з можливістю скасування
                result = await loop.run_in_executor(None, future.result)
                return result
        except asyncio.CancelledError:
            print("[DEBUG] Транскрипцію скасовано")
            return None
        except Exception as e:
            print(f"[DEBUG] Async помилка транскрипції: {e}")
            return None

    async def listen_with_silence_detection(self, max_timeout, silence_timeout):
        """
        Покращена детекція тиші з кращим захопленням повних фраз.
        max_timeout - максимальний час слухання взагалі.
        silence_timeout - час тиші після якого зупиняється.
        """
        start_time = asyncio.get_event_loop().time()

        # Збільшуємо час для одного слухання, щоб краще захоплювати повні фрази
        listen_chunk_time = min(max_timeout, 5.0)  # Максимум 5 секунд за раз

        while True:
            current_time = asyncio.get_event_loop().time()

            # Перевіряємо чи не вийшов загальний таймаут
            if current_time - start_time > max_timeout:
                print(f"[DEBUG] Досягнуто максимальний таймаут {max_timeout}с")
                return None

            remaining_time = min(
                max_timeout - (current_time - start_time),
                listen_chunk_time
            )

            if remaining_time <= 0:
                print(f"[DEBUG] Час сесії вичерпано")
                return None

            # Слухаємо довші інтервали для кращого захоплення речень
            transcript = await self.listen_and_transcribe_async(remaining_time)

            if transcript and transcript.strip():
                print(f"[DEBUG] Отримано транскрипт: '{transcript.strip()}'")
                return transcript.strip()

            # Якщо тишу вже довго, завершуємо
            if current_time - start_time > silence_timeout:
                print(f"[DEBUG] Тривала тиша {silence_timeout}с - завершення слухання")
                return None

            # Коротка пауза перед наступною спробою
            await asyncio.sleep(0.2)