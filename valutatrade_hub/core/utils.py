import json
import os
from typing import List, Dict, Any


DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')

USERS_FILE = os.path.join(DATA_DIR, 'users.json')
PORTFOLIOS_FILE = os.path.join(DATA_DIR, 'portfolios.json')
RATES_FILE = os.path.join(DATA_DIR, 'rates.json')
SESSION_FILE = os.path.join(DATA_DIR, '.session')


def load_data(file_path: str) -> Any:
    """Загружает данные из JSON-файла."""
    if not os.path.exists(file_path):
        return [] if 'users' in file_path or 'portfolios' in file_path else {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        print(f"Ошибка загрузки файла {file_path}")
        return [] if file_path.endswith('s.json') else {}


def save_data(file_path: str, data: Any):
    """Сохраняет данные в JSON-файл."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_current_user_id() -> int | None:
    """Получает ID залогиненного пользователя из сессионного файла."""
    if not os.path.exists(SESSION_FILE):
        print(f"Warning!: session file not found.{SESSION_FILE}")
        return None
    with open(SESSION_FILE, 'r') as f:
        try:
            return int(f.read().strip())
        except ValueError:
            return None


def set_current_user(user_id: int):
    """Записывает ID залогиненного пользователя в сессионный файл."""
    with open(SESSION_FILE, 'w') as f:
        f.write(str(user_id))


def logout_user():
    """Удаляет сессионный файл."""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
