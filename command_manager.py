from logger_config import get_logger
import smart_ai

logger = get_logger('command_manager')


class CommandManager:
    """Bridge між old code та smart AI системою."""

    def __init__(self, plugins_dir="plugins"):
        logger.info("Command manager initialized (smart AI mode)")

    async def find_command(self, text):
        """Шукає команду тільки через ШІ асистента."""

        # Тільки Smart AI обробка
        if smart_ai.smart_assistant:
            ai_result = await smart_ai.process_smart_command(text)
            if ai_result.get("success"):
                logger.info("Smart plugin command processed", extra={
                    'action_type': ai_result.get('action', {}).get('type'),
                    'successful_count': ai_result.get('action', {}).get('successful_count', 0),
                    'total_count': ai_result.get('action', {}).get('total_count', 0)
                })
                return {'smart_ai': ai_result, 'type': 'smart_ai', 'original_text': text}, None

        logger.debug("No smart assistant available", extra={'text': text})
        return None, None

    async def execute_command(self, command, argument=None):
        """Виконує команду тільки через Smart AI систему."""

        # Тільки Smart AI команда
        if isinstance(command, dict) and command.get('type') == 'smart_ai':
            ai_result = command.get('smart_ai', {})

            if ai_result.get('success'):
                return {
                    'success': True,
                    'response_text': ai_result.get('message', 'Smart AI команду виконано')
                }
            else:
                return {
                    'success': False,
                    'response_text': ai_result.get('message', 'Smart AI команда не вдалася')
                }

        # Fallback для невідомих команд
        logger.warning("Unsupported command type", extra={'command_type': type(command)})
        return {
            'success': False,
            'response_text': 'Підтримуються тільки Smart AI команди'
        }