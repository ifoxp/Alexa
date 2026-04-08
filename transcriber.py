import speech_recognition as sr
import settings
import asyncio
import concurrent.futures
import threading
import struct
import math
import pyaudio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from logger_config import get_logger
import os
from datetime import datetime
logger = get_logger('transcriber')

def _find_sr_microphone_index(device_name: str):
    """Знаходить device_index для speech_recognition за назвою мікрофону з config.json."""
    if not device_name:
        return None
    for i, name in enumerate(sr.Microphone.list_microphone_names()):
        if device_name.lower() in name.lower():
            return i
    return None


class OnlineTranscriber:
    def __init__(self):
        self.recognizer = sr.Recognizer()

        # Беремо мікрофон і мови з config.json
        import config_manager as cfg
        try:
            _config = cfg.load_config()
            self.languages = _config.get("languages", ["uk-UA", "ru-RU", "en-US"])
            if not self.languages:
                self.languages = ["uk-UA", "ru-RU", "en-US"]
            mic_name = _config.get("microphoneDevice", "")
        except Exception:
            self.languages = ["uk-UA", "ru-RU", "en-US"]
            mic_name = ""

        mic_index = _find_sr_microphone_index(mic_name)
        self.microphone = sr.Microphone(
            device_index=mic_index,
            sample_rate=settings.RATE,
            chunk_size=settings.CHUNK
        )
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
            
            self.recognizer.pause_threshold = 0.8
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

        import speed_logger
        timer = speed_logger.get_session()
        if timer:
            timer.on_listen_start()

        with self.microphone as source:
            try:
                print(f" M... (очікую до {timeout:.1f}с)")
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=20,
                )
            except sr.WaitTimeoutError:
                return None
            

        if timer:
            timer.on_audio_ready(len(audio.frame_data))
            timer.on_stt_start()

        result = self._recognize_with_retry(audio)

        if timer:
            timer.on_stt_done(result or "")

        return result

    def listen_and_get_audio(self, timeout,
                              pause_threshold: float = 0.8,
                              speech_start_timeout: float = 8.0,
                              min_speech_duration: float = 0.3):
        """Слухає одну фразу з власним VAD і повертає WAV байти для Gemini Native Audio.

        Зупиняється як тільки виявляє тишу тривалістю pause_threshold після початку мови.
        speech_start_timeout — скільки чекати початку мови (не більше timeout).
        min_speech_duration — мінімальна тривалість мови щоб не повертати сміття.
        """
        if not timeout or timeout <= 0:
            return None

        import speed_logger
        import wave
        import io
        timer = speed_logger.get_session()
        if timer:
            timer.on_listen_start()

        rate = settings.RATE
        chunk = settings.CHUNK
        fmt = pyaudio.paInt16
        channels = 1

        # Поріг RMS для детекції мови — беремо з recognizer (він вже скалібрований)
        energy_threshold = max(self.recognizer.energy_threshold, 150)

        pa = pyaudio.PyAudio()

        # Знаходимо device_index через мікрофон speech_recognition
        device_index = self.microphone.device_index

        sample_width = pa.get_sample_size(fmt)

        try:
            stream = pa.open(
                format=fmt,
                channels=channels,
                rate=rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=chunk,
            )
        except Exception as e:
            pa.terminate()
            logger.error(f"VAD: не вдалось відкрити мікрофон: {e}")
            return None

        chunks_per_second = rate / chunk  # ~31 чанків/с при rate=16000, chunk=512
        pause_chunks = int(pause_threshold * chunks_per_second)
        start_timeout_chunks = int(min(speech_start_timeout, timeout) * chunks_per_second)
        max_chunks = int(timeout * chunks_per_second)

        frames = []
        speech_started = False
        silence_count = 0
        total_chunks = 0
        speech_chunks = 0

        print(f" M... (VAD, очікую до {timeout:.1f}с, поріг={energy_threshold:.0f})")

        try:
            while total_chunks < max_chunks:
                data = stream.read(chunk, exception_on_overflow=False)
                total_chunks += 1

                # RMS енергія чанку
                shorts = struct.unpack(f"{len(data) // 2}h", data)
                rms = math.sqrt(sum(s * s for s in shorts) / len(shorts)) if shorts else 0

                is_speech = rms > energy_threshold

                if is_speech:
                    if not speech_started:
                        speech_started = True
                        print(f" [VAD] Мова виявлена (RMS={rms:.0f})")
                    silence_count = 0
                    frames.append(data)
                    speech_chunks += 1
                elif speech_started:
                    # Тиша після початку мови
                    silence_count += 1
                    frames.append(data)  # захоплюємо "хвіст"
                    if silence_count >= pause_chunks:
                        print(f" [VAD] Тиша {pause_threshold}s — зупиняємо запис")
                        break
                else:
                    # Тиша до початку мови
                    if total_chunks >= start_timeout_chunks:
                        print(f" [VAD] Мова не виявлена за {speech_start_timeout:.0f}с — таймаут")
                        break
        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()

        if not speech_started or speech_chunks < int(min_speech_duration * chunks_per_second):
            return None

        # Збираємо WAV в пам'яті
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(b"".join(frames))
        wav = buf.getvalue()

        if timer:
            timer.on_audio_ready(len(wav))
        return wav

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
    def _save_debug_audio(self, audio, prefix="audio"):
        """Тимчасове збереження аудіофайлу для аналізу (дебаг)"""
        try:
            # Створюємо папку в logs, якщо її ще немає
            os.makedirs("logs/audio_debug", exist_ok=True)
            
            # Генеруємо унікальне ім'я з таймстемпом
            timestamp = datetime.now().strftime("%H-%M-%S")
            filepath = f"logs/audio_debug/{prefix}_{timestamp}.wav"
            
            # Зберігаємо сирі байти у WAV файл
            with open(filepath, "wb") as f:
                f.write(audio.get_wav_data())
                
            print(f"🎧 [DEBUG AUDIO] Збережено: {filepath}")
        except Exception as e:
            print(f"🎧 [DEBUG AUDIO] Помилка збереження: {e}")