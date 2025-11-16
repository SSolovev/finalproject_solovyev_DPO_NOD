# valutatrade_hub/parser_service/updater.py
import logging
from datetime import datetime, timezone
from typing import List

from ..core.exceptions import ApiRequestError
from .api_clients import BaseApiClient, CoinGeckoClient, ExchangeRateApiClient
from .config import parser_config
from .storage import RatesStorage


class RatesUpdater:
    """Координирует процесс обновления курсов от всех клиентов."""

    def __init__(self, clients: List[BaseApiClient], storage: RatesStorage):
        self.clients = clients
        self.storage = storage

    def run_update(self, source_filter: str = None):
        """
        Запускает процесс обновления курсов.
        :param source_filter: Если указан, обновляет только от этого источника.
        """
        logging.info("Starting rates update...")
        all_fetched_rates = {}
        history_records = []

        clients_to_run = self.clients
        if source_filter:
            source_filter = source_filter.lower()
            clients_to_run = [
                c for c in self.clients
                if c.__class__.__name__.lower().startswith(source_filter)
            ]
            if not clients_to_run:
                logging.warning(f"No clients found for source filter: {source_filter}")
                return

        for client in clients_to_run:
            source_name = client.__class__.__name__.replace("Client", "")
            try:
                rates = client.fetch_rates()
                # Формируем данные для кэша и истории
                now_ts = datetime.now(timezone.utc).isoformat()
                for pair_key, rate in rates.items():
                    # Для кэша
                    all_fetched_rates[pair_key] = {
                        "rate": rate,
                        "updated_at": now_ts,
                        "source": source_name
                    }
                    # Для истории
                    from_curr, to_curr = pair_key.split('_')
                    history_records.append({
                        "id": f"{pair_key}_{now_ts}",
                        "from_currency": from_curr,
                        "to_currency": to_curr,
                        "rate": rate,
                        "timestamp": now_ts,
                        "source": source_name
                    })

            except ApiRequestError as e:
                logging.error(f"Failed to fetch from {source_name}: {e}")

        if all_fetched_rates:
            self.storage.save_rates_cache(all_fetched_rates)
            self.storage.append_to_history(history_records)
            logging.info(f"Update finished. "
                         f"Total rates processed: {len(all_fetched_rates)}.")
        else:
            logging.warning("Update finished, but no new rates were fetched.")


def get_default_updater() -> RatesUpdater:
    """Фабричная функция для создания RatesUpdater с настройками по умолчанию."""
    clients = [CoinGeckoClient(), ExchangeRateApiClient()]
    storage = RatesStorage(
        cache_path=parser_config.RATES_FILE_PATH,
        history_path=parser_config.HISTORY_FILE_PATH
    )
    return RatesUpdater(clients, storage)
