# valutatrade_hub/infra/database.py
import json
import os
from typing import Any, Dict, List

from .settings import settings


class DatabaseManager:
    """
    Singleton для управления доступом к файловому хранилищу (JSON).
    Абстрагирует логику чтения и записи, используя пути из SettingsLoader.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._init_paths()
        return cls._instance

    def _init_paths(self):
        """Инициализирует пути к файлам данных."""
        data_path = settings.get("data_path", "data")
        self.users_file = os.path.join(data_path,
                                       settings.get("users_file",
                                                    "users.json"))
        self.portfolios_file = os.path.join(data_path,
                                            settings.get("portfolios_file",
                                                         "portfolios.json"))
        self.rates_file = os.path.join(data_path,
                                       settings.get("rates_file",
                                                    "rates.json"))
        self.session_file = os.path.join(data_path, ".session")
        os.makedirs(data_path, exist_ok=True)

    def _load_data(self, file_path: str) -> Any:
        if not os.path.exists(file_path):
            return [] if 'users' in file_path or 'portfolios' in file_path else {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return [] if 'users' in file_path or 'portfolios' in file_path else {}

    def _save_data(self, file_path: str, data: Any):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_users(self) -> List[Dict]:
        return self._load_data(self.users_file)

    def save_users(self, users_data: List[Dict]):
        self._save_data(self.users_file, users_data)

    def load_portfolios(self) -> List[Dict]:
        return self._load_data(self.portfolios_file)

    def save_portfolios(self, portfolios_data: List[Dict]):
        self._save_data(self.portfolios_file, portfolios_data)

    def load_rates(self) -> Dict:
        return self._load_data(self.rates_file)

    def save_rates(self, rates_data: Dict):
        self._save_data(self.rates_file, rates_data)

    def get_current_user_id(self) -> int | None:
        if not os.path.exists(self.session_file):
            return None
        with open(self.session_file, 'r') as f:
            try:
                return int(f.read().strip())
            except ValueError:
                return None

    def set_current_user(self, user_id: int):
        with open(self.session_file, 'w') as f:
            f.write(str(user_id))

    def logout_user(self):
        if os.path.exists(self.session_file):
            os.remove(self.session_file)


db_manager = DatabaseManager()
