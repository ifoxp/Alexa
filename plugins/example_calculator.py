# example_calculator.py - Приклад користувацького плагіна
from typing import Dict, Any
from .base_plugin import SmartPlugin


class CalculatorPlugin(SmartPlugin):
    """Простий калькулятор для демонстрації можливостей плагінів."""

    @property
    def name(self) -> str:
        return "calculator"

    @property
    def description(self) -> str:
        return "Математичні розрахунки: додавання, віднімання, множення. Приклад користувацького плагіна."

    @property
    def commands(self) -> Dict[str, str]:
        return {
            "add": "додати числа (наприклад: 5 плюс 3)",
            "subtract": "відняти числа (наприклад: 10 мінус 4)",
            "multiply": "помножити числа (наприклад: 6 на 7)"
        }

    async def execute_command(self, command_name: str, **kwargs) -> Dict[str, Any]:
        """Виконує математичні операції."""
        try:
            value = kwargs.get("value", "")
            if not value:
                return {
                    "success": False,
                    "result": None,
                    "message": "Не вказано числа для обчислення"
                }

            # Витягуємо числа з тексту
            import re
            numbers = [float(x) for x in re.findall(r'-?\d+\.?\d*', value)]

            if len(numbers) < 2:
                return {
                    "success": False,
                    "result": None,
                    "message": f"Знайдено тільки {len(numbers)} чисел, потрібно щонайменше 2"
                }

            if command_name == "add":
                result = sum(numbers)
                operation = "+"
                self.log_info(f"Addition: {' + '.join(map(str, numbers))} = {result}")

            elif command_name == "subtract":
                result = numbers[0]
                for num in numbers[1:]:
                    result -= num
                operation = "-"
                self.log_info(f"Subtraction: {' - '.join(map(str, numbers))} = {result}")

            elif command_name == "multiply":
                result = 1
                for num in numbers:
                    result *= num
                operation = "*"
                self.log_info(f"Multiplication: {' * '.join(map(str, numbers))} = {result}")

            else:
                return {
                    "success": False,
                    "result": None,
                    "message": f"Невідома операція: {command_name}"
                }

            return {
                "success": True,
                "result": {
                    "numbers": numbers,
                    "operation": operation,
                    "result": result
                },
                "message": f"Результат: {result}"
            }

        except ValueError as e:
            self.log_error(f"Invalid numbers in calculator", error=str(e))
            return {
                "success": False,
                "result": None,
                "message": "Не вдалося розпізнати числа. Спробуйте: 'додай 5 плюс 3'"
            }

        except Exception as e:
            self.log_error(f"Calculator error in {command_name}", error=str(e))
            return {
                "success": False,
                "result": None,
                "message": f"Помилка калькулятора: {str(e)}"
            }