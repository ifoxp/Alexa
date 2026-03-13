# memory_manager.py
import threading
import weakref
import gc
from logger_config import get_logger

logger = get_logger('memory_manager')

class MemoryManager:
    """Керує пам'яттю та ресурсами асистента."""

    def __init__(self):
        self.resources = []
        self.lock = threading.Lock()
        self.cleanup_callbacks = []

    def register_resource(self, resource, cleanup_func=None):
        """Реєструє ресурс для автоматичного очищення."""
        with self.lock:
            if cleanup_func:
                # Використовуємо weakref щоб уникнути циклічних посилань
                self.resources.append((weakref.ref(resource), cleanup_func))
            else:
                # Стандартний cleanup через context manager
                self.resources.append((weakref.ref(resource), None))

            # Видаляємо спам логування resource registered

    def add_cleanup_callback(self, callback):
        """Додає callback для виконання під час очищення."""
        with self.lock:
            self.cleanup_callbacks.append(callback)

    def cleanup_dead_resources(self):
        """Видаляє посилання на мертві об'єкти."""
        with self.lock:
            alive_resources = []
            cleaned_count = 0

            for resource_ref, cleanup_func in self.resources:
                if resource_ref() is not None:
                    alive_resources.append((resource_ref, cleanup_func))
                else:
                    cleaned_count += 1

            self.resources = alive_resources

            if cleaned_count > 0:
                logger.debug("Dead resources cleaned", extra={
                    'cleaned': cleaned_count,
                    'remaining': len(self.resources)
                })

    def force_cleanup_all(self):
        """Примусово очищує всі зареєстровані ресурси."""
        logger.info("Starting force cleanup of all resources")

        with self.lock:
            # Виконуємо custom cleanup callbacks
            for callback in self.cleanup_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error("Cleanup callback error", extra={'error': str(e)})

            # Очищуємо зареєстровані ресурси
            for resource_ref, cleanup_func in self.resources:
                resource = resource_ref()
                if resource is not None:
                    try:
                        if cleanup_func:
                            cleanup_func(resource)
                        elif hasattr(resource, 'close'):
                            resource.close()
                        elif hasattr(resource, '__exit__'):
                            resource.__exit__(None, None, None)
                    except Exception as e:
                        logger.error("Resource cleanup error", extra={
                            'resource_type': type(resource).__name__,
                            'error': str(e)
                        })

            # Очищуємо списки
            self.resources.clear()
            self.cleanup_callbacks.clear()

        # Примусова збірка сміття
        collected = gc.collect()
        logger.info("Memory cleanup completed", extra={
            'garbage_collected': collected
        })

    def get_memory_stats(self):
        """Повертає статистику пам'яті."""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()

        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            'percent': process.memory_percent(),
            'registered_resources': len(self.resources),
            'gc_objects': len(gc.get_objects())
        }


class ResourceManager:
    """Context manager для автоматичного керування ресурсами."""

    def __init__(self, memory_manager: MemoryManager):
        self.memory_manager = memory_manager
        self.managed_resources = []

    def add(self, resource, cleanup_func=None):
        """Додає ресурс під управління."""
        self.managed_resources.append((resource, cleanup_func))
        self.memory_manager.register_resource(resource, cleanup_func)
        return resource

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Автоматично очищає всі ресурси при виході з контексту."""
        for resource, cleanup_func in self.managed_resources:
            try:
                if cleanup_func:
                    cleanup_func(resource)
                elif hasattr(resource, 'close'):
                    resource.close()
                elif hasattr(resource, '__exit__'):
                    resource.__exit__(exc_type, exc_val, exc_tb)
            except Exception as e:
                logger.error("Resource cleanup error in context", extra={
                    'resource_type': type(resource).__name__,
                    'error': str(e)
                })

        self.managed_resources.clear()


# Глобальний memory manager
memory_manager = MemoryManager()


def auto_cleanup(cleanup_func=None):
    """Декоратор для автоматичного очищення ресурсів."""
    def decorator(cls):
        original_init = cls.__init__

        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            memory_manager.register_resource(self, cleanup_func)

        cls.__init__ = new_init
        return cls

    return decorator


def log_memory_usage(operation_name):
    """Декоратор для логування використання пам'яті."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            stats_before = memory_manager.get_memory_stats()

            result = func(*args, **kwargs)

            stats_after = memory_manager.get_memory_stats()
            memory_diff = stats_after['rss_mb'] - stats_before['rss_mb']

            if abs(memory_diff) > 1.0:  # Логуємо тільки значні зміни
                logger.info("Memory usage change", extra={
                    'operation': operation_name,
                    'memory_change_mb': round(memory_diff, 2),
                    'current_memory_mb': round(stats_after['rss_mb'], 2)
                })

            return result

        return wrapper
    return decorator