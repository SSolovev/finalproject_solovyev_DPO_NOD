# valutatrade_hub/parser_service/config.py
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class ParserConfig:
    """Конфигурация для сервиса парсинга."""

    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY")

    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    BASE_CURRENCY: str = "USD"
    FIAT_CURRENCIES: tuple = ("EUR", "GBP", "RUB")
    CRYPTO_CURRENCIES: tuple = ("BTC", "ETH", "SOL")
    CRYPTO_ID_MAP = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana"}

    RATES_FILE_PATH: str = "data/rates.json"
    HISTORY_FILE_PATH: str = "data/exchange_rates.json"

    REQUEST_TIMEOUT: int = 10


parser_config = ParserConfig()

if not parser_config.EXCHANGERATE_API_KEY:
    raise ValueError(
        "API-ключ для ExchangeRate-API не найден. "
        "Убедитесь, что он задан в переменной окружения "
        "EXCHANGERATE_API_KEY или в файле .env"
    )
