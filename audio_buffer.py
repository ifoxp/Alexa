# audio_buffer.py
import collections
import threading
import time
from logger_config import get_logger

logger = get_logger('audio_buffer')

class AudioBuffer:
    """Ring buffer для аудіо даних з thread-safe доступом."""

    def __init__(self, max_size=8192):
        self.buffer = collections.deque(maxlen=max_size)
        self.condition = threading.Condition()
        self.is_active = True
        self.stats = {
            'writes': 0,
            'reads': 0,
            'overflows': 0,
            'underflows': 0
        }

    def write(self, audio_data):
        """Додає аудіо дані в буфер."""
        if not self.is_active:
            return

        with self.condition:
            old_size = len(self.buffer)

            # Додаємо дані (deque автоматично видалить старі при переповненні)
            for sample in audio_data:
                self.buffer.append(sample)

            # Статистика
            self.stats['writes'] += 1
            if old_size == self.buffer.maxlen and len(audio_data) > 0:
                self.stats['overflows'] += 1
                # Видаляємо спам-логування overflow

            # Сповіщуємо читачів
            self.condition.notify_all()

    def read_frame(self, frame_size, timeout=None):
        """Читає кадр заданого розміру з буфера."""
        if not self.is_active:
            return None

        with self.condition:
            start_time = time.time()

            while len(self.buffer) < frame_size and self.is_active:
                if timeout and (time.time() - start_time) >= timeout:
                    self.stats['underflows'] += 1
                    # Видаляємо спам timeout логи
                    return None

                self.condition.wait(timeout=0.1)

            if not self.is_active:
                return None

            # Читаємо дані
            frame = []
            for _ in range(frame_size):
                if self.buffer:
                    frame.append(self.buffer.popleft())
                else:
                    break

            self.stats['reads'] += 1

            if len(frame) < frame_size:
                self.stats['underflows'] += 1
                # Видаляємо спам underflow логи

            return frame if frame else None

    def get_available_samples(self):
        """Повертає кількість доступних семплів."""
        with self.condition:
            return len(self.buffer)

    def clear(self):
        """Очищає буфер."""
        with self.condition:
            self.buffer.clear()
            self.condition.notify_all()
            # Видаляємо debug лог cleared

    def stop(self):
        """Зупиняє буфер."""
        with self.condition:
            self.is_active = False
            self.condition.notify_all()
            logger.info("Audio buffer stopped", extra=self.stats)

    def get_stats(self):
        """Повертає статистику буфера."""
        return self.stats.copy()


class BufferedAudioStream:
    """Wrapper для PyAudio stream з буферизацією."""

    def __init__(self, pyaudio_stream, buffer_size=8192):
        self.stream = pyaudio_stream
        self.buffer = AudioBuffer(buffer_size)
        self.is_running = False
        self.reader_thread = None

    def start_buffering(self):
        """Запускає буферизацію в окремому потоці."""
        if self.is_running:
            return

        self.is_running = True
        self.reader_thread = threading.Thread(
            target=self._buffer_loop,
            daemon=True
        )
        self.reader_thread.start()
        logger.info("Audio buffering started")

    def _buffer_loop(self):
        """Головний цикл читання з потоку в буфер."""
        # Видаляємо debug лог loop started

        while self.is_running:
            try:
                if self.stream.is_active():
                    # Читаємо невеликими блоками для зменшення latency
                    chunk_size = 512
                    audio_data = self.stream.read(chunk_size, exception_on_overflow=False)

                    # Конвертуємо bytes в int16
                    import struct
                    samples = struct.unpack(f"<{chunk_size}h", audio_data)

                    # Додаємо в буфер
                    self.buffer.write(samples)
                else:
                    time.sleep(0.01)

            except Exception as e:
                logger.error("Audio buffer loop error", extra={'error': str(e)})
                time.sleep(0.1)

        # Видаляємо debug лог loop stopped

    def read_frame(self, frame_size, timeout=1.0):
        """Читає кадр з буфера."""
        return self.buffer.read_frame(frame_size, timeout)

    def stop_buffering(self):
        """Зупиняє буферизацію."""
        if not self.is_running:
            return

        self.is_running = False
        self.buffer.stop()

        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=2.0)

        logger.info("Audio buffering stopped", extra=self.buffer.get_stats())

    def get_buffer_stats(self):
        """Повертає статистику буфера."""
        return self.buffer.get_stats()

    def is_active(self):
        """Перевіряє чи активний потік."""
        return self.stream.is_active() if self.stream else False

    def close(self):
        """Закриває буферизований потік."""
        self.stop_buffering()
        if self.stream:
            try:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                # Видаляємо debug лог stream close error
                pass
        logger.info("Buffered audio stream closed")