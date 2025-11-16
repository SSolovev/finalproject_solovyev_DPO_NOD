from abc import ABC, abstractmethod
from typing import Dict

from valutatrade_hub.core.exceptions import CurrencyNotFoundError


class Currency(ABC):
    """
    Абстрактный базовый класс для представления валюты.
    """
    def __init__(self, name: str, code: str):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Имя валюты не может быть пустым.")
        if not isinstance(code, str) or not (2 <= len(code) <= 5) or ' ' in code:
            raise ValueError("Код валюты должен быть строкой "
                             "из 2-5 символов без пробелов.")

        self.name: str = name
        self.code: str = code.upper()

    @abstractmethod
    def get_display_info(self) -> str:
        """Возвращает строковое представление валюты для UI."""
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}({self.code})>"


class FiatCurrency(Currency):
    """Представляет фиатную валюту."""
    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)
        self.issuing_country: str = issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """Представляет криптовалюту."""
    def __init__(self, name: str, code: str, algorithm: str, market_cap: float):
        super().__init__(name, code)
        self.algorithm: str = algorithm
        self.market_cap: float = market_cap

    def get_display_info(self) -> str:
        return (f"[CRYPTO] {self.code} — {self.name} "
                f"(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})")


# --- Реестр валют (Фабрика) ---
_CURRENCIES: Dict[str, Currency] = {
    "USD": FiatCurrency(name="US Dollar", code="USD", issuing_country="United States"),
    "EUR": FiatCurrency(name="Euro", code="EUR", issuing_country="Eurozone"),
    "RUB": FiatCurrency(name="Russian Ruble", code="RUB", issuing_country="Russia"),
    "BTC": CryptoCurrency(name="Bitcoin", code="BTC", algorithm="SHA-256",
                          market_cap=1.12e12),
    "ETH": CryptoCurrency(name="Ethereum", code="ETH", algorithm="Ethash",
                          market_cap=4.5e11),
}


def get_currency(code: str) -> Currency:
    """
    Фабричный метод для получения объекта валюты по её коду.

    :param code: Код валюты (например, "USD", "BTC").
    :return: Объект класса Currency или его наследника.
    :raises CurrencyNotFoundError: Если валюта с таким кодом не найдена.
    """
    currency = _CURRENCIES.get(code.upper())
    if currency is None:
        raise CurrencyNotFoundError(f"Валюта с кодом '{code.upper()}' "
                                    f"не найдена в реестре.")
    return currency
