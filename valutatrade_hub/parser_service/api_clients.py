# valutatrade_hub/parser_service/api_clients.py
import logging
from abc import ABC, abstractmethod
from typing import Dict

import requests
from requests.exceptions import RequestException

from ..core.exceptions import ApiRequestError
from .config import parser_config


class BaseApiClient(ABC):
    """Абстрактный базовый класс для API-клиентов."""

    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """
        Получает курсы валют и возвращает их в стандартизированном формате.
        Формат: {"<FROM>_<TO>": rate}
        """
        pass


class CoinGeckoClient(BaseApiClient):
    """Клиент для API CoinGecko."""

    def fetch_rates(self) -> Dict[str, float]:
        logging.info("Fetching rates from CoinGecko...")
        ids = ",".join(parser_config.CRYPTO_ID_MAP.values())
        params = {
            "ids": ids,
            "vs_currencies": parser_config.BASE_CURRENCY.lower(),
        }

        try:
            response = requests.get(
                parser_config.COINGECKO_URL,
                params=params,
                timeout=parser_config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            standardized_rates = {}
            reverse_map = {v: k for k, v in parser_config.CRYPTO_ID_MAP.items()}
            for crypto_id, rates in data.items():
                rate = rates.get(parser_config.BASE_CURRENCY.lower())
                if rate is not None:
                    crypto_code = reverse_map.get(crypto_id)
                    if crypto_code:
                        pair_key = f"{crypto_code}_{parser_config.BASE_CURRENCY}"
                        standardized_rates[pair_key] = float(rate)

            logging.info(f"CoinGecko: "
                         f"Successfully fetched {len(standardized_rates)} rates.")
            return standardized_rates

        except RequestException as e:
            raise ApiRequestError(f"CoinGecko request failed: {e}")
        except (KeyError, ValueError) as e:
            raise ApiRequestError(f"CoinGecko data parsing failed: {e}")


class ExchangeRateApiClient(BaseApiClient):
    """Клиент для API ExchangeRate-API."""

    def fetch_rates(self) -> Dict[str, float]:
        logging.info("Fetching rates from ExchangeRate-API...")
        url = (
            f"{parser_config.EXCHANGERATE_API_URL}/"
            f"{parser_config.EXCHANGERATE_API_KEY}/latest/{parser_config.BASE_CURRENCY}"
        )

        try:
            response = requests.get(url, timeout=parser_config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if data.get("result") != "success":
                error_type = data.get("error-type", "unknown_error")
                raise ApiRequestError(f"ExchangeRate-API "
                                      f"returned an error: {error_type}")

            all_rates = data.get("conversion_rates", {})
            standardized_rates = {}
            for currency in parser_config.FIAT_CURRENCIES:
                rate = all_rates.get(currency)
                if rate is not None:
                    if rate == 0:
                        continue
                    pair_key = f"{currency}_{parser_config.BASE_CURRENCY}"
                    standardized_rates[pair_key] = 1 / float(rate)

            logging.info(f"ExchangeRate-API: "
                         f"Successfully fetched {len(standardized_rates)} rates.")
            return standardized_rates

        except RequestException as e:
            raise ApiRequestError(f"ExchangeRate-API request failed: {e}")
        except (KeyError, ValueError, ZeroDivisionError) as e:
            raise ApiRequestError(f"ExchangeRate-API data parsing failed: {e}")
