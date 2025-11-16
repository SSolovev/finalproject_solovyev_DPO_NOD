# valutatrade_hub/core/exceptions.py

class BaseTradeError(Exception):
    """Базовый класс для всех исключений проекта."""
    pass

class InsufficientFundsError(BaseTradeError):
    """Вызывается при нехватке средств на кошельке."""
    def __init__(self, available: float, required: float, code: str):
        self.available = available
        self.required = required
        self.code = code
        super().__init__(
            f"Недостаточно средств: доступно {available:.4f} {code}, требуется {required:.4f} {code}"
        )

class CurrencyNotFoundError(BaseTradeError):
    """Вызывается, когда валюта не найдена в реестре."""
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Валюта с кодом '{code}' не найдена в реестре.")

class ApiRequestError(BaseTradeError):
    """Вызывается при ошибках взаимодействия с внешними сервисами (например, парсером)."""
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")