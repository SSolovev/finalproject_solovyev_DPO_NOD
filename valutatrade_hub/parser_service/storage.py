# valutatrade_hub/parser_service/storage.py
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from typing import Dict, List


class RatesStorage:
    """Управляет сохранением курсов в файлы кэша и истории."""

    def __init__(self, cache_path: str, history_path: str):
        self.cache_path = cache_path
        self.history_path = history_path
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        os.makedirs(os.path.dirname(history_path), exist_ok=True)

    def _atomic_write(self, file_path: str, data: dict):
        """Атомарная запись в файл через временный файл."""
        temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(file_path))
        try:
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, file_path)
            logging.info(f"Successfully saved data to {file_path}")
        except Exception as e:
            os.remove(temp_path)
            logging.error(f"Failed to write to {file_path}: {e}")
            raise

    def save_rates_cache(self, rates_data: Dict[str, dict]):
        """Сохраняет актуальные курсы в rates.json."""
        cache_content = {
            "pairs": rates_data,
            "last_refresh": datetime.now(timezone.utc).isoformat()
        }
        self._atomic_write(self.cache_path, cache_content)

    def append_to_history(self, new_records: List[dict]):
        """Добавляет новые записи в history.json."""
        try:
            if os.path.exists(self.history_path):
                with open(self.history_path, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            else:
                history = []
        except (json.JSONDecodeError, FileNotFoundError):
            history = []

        history.extend(new_records)
        self._atomic_write(self.history_path, history)
