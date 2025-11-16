# valutatrade_hub/decorators.py
import logging
from functools import wraps
from typing import Any, Callable


def log_action(action_name: str, verbose: bool = False) -> Callable:
    """
    Декоратор для логирования выполнения ключевых операций.
    Логирует начало, результат (успех/ошибка) и основные параметры.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            user = kwargs.get('user')
            username = user.username if user else 'Guest'

            # Собираем основные аргументы для лога
            log_params = {
                'username': username,
                'currency': kwargs.get('currency', 'N/A'),
                'amount': kwargs.get('amount', 'N/A')
            }
            log_str = ' '.join(f"{k}='{v}'" for k, v in log_params.items()
                               if v != 'N/A')

            try:
                # Логируем вызов
                logging.info(f"START {action_name} {log_str}")

                result = func(*args, **kwargs)

                # Формируем сообщение об успехе
                success_log = f"{action_name} {log_str} result=OK"
                if verbose and isinstance(result, dict):
                    # Добавляем доп. инфо для verbose режима
                    rate = result.get('rate', 0)
                    success_log += (f" rate={rate:.2f} "
                                    f"base='{result.get('base_currency', 'N/A')}'")

                logging.info(f"FINISH {success_log}")
                return result

            except Exception as e:
                # Логируем ошибку
                error_type = type(e).__name__
                logging.error(
                    f"FINISH {action_name} {log_str} result=ERROR "
                    f"error_type='{error_type}' error_message='{e}'"
                )
                # Пробрасываем исключение дальше
                raise

        return wrapper

    return decorator
