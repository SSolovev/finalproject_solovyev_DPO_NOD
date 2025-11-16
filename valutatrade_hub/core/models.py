import hashlib
import os
from datetime import datetime
from typing import Dict

from valutatrade_hub.core.exceptions import InsufficientFundsError


class User:
    """Пользователь системы."""

    def __init__(self, user_id: int, username: str, password: str, salt: str = None,
                 registration_date: datetime = None):
        self._user_id = user_id
        self._username = username
        self._salt = salt or os.urandom(16).hex()
        self._hashed_password = self._hash_password(password, self._salt)
        self._registration_date = registration_date or datetime.now()

    def get_user_info(self) -> str:
        """Выводит информацию о пользователе."""
        return f"ID: {self._user_id}, Имя: {self._username}, Дата регистрации: {self._registration_date.strftime('%Y-%m-%d %H:%M')}"

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым.")
        self._username = value.strip()

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    def _hash_password(self, password: str, salt: str) -> str:
        """Хеширование пароля с солью."""
        if len(password) < 4:
            raise ValueError('Пароль должен быть не короче 4 символов ')
        return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

    def change_password(self, new_password: str):
        self._hashed_password = self._hash_password(new_password, self._salt)
        print("Пароль успешно изменен.")

    def verify_password(self, password: str) -> bool:
        return self._hashed_password == self._hash_password(password, self._salt)

    def to_dict(self) -> dict:
        """Сериализация объекта в словарь."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat(),
            "hashed_password": self._hashed_password
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """Десериализация объекта из словаря."""

        user = cls(
            user_id=data['user_id'],
            username=data['username'],
            password="dummy_password_on_load"
        )
        user._hashed_password = data['hashed_password']
        user._salt = data['salt']
        user._registration_date = datetime.fromisoformat(data['registration_date'])
        return user


class Wallet:
    """Кошелёк пользователя для одной конкретной валюты."""

    def __init__(self, currency_code: str, balance: float = 0.0):
        self.currency_code = currency_code.upper()
        self._balance = float(balance)

    @property
    def balance(self) -> float:
        """Геттер для получения текущего баланса."""
        return self._balance

    @balance.setter
    def balance(self, value: float):
        """Сеттер для установки баланса с проверкой."""
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом.")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным.")
        self._balance = float(value)

    def deposit(self, amount: float):
        """Пополнение баланса."""
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительным числом.")
        self.balance += amount
        print(f"Баланс {self.currency_code} пополнен на {amount:.4f}. Текущий баланс: {self.balance:.4f}")

    def withdraw(self, amount: float):
        """Снятие средств с баланса."""
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Сумма снятия должна быть положительным числом.")
        if amount > self.balance:
            raise ValueError(f"Недостаточно средств. Доступно: {self.balance:.4f} {self.currency_code}")
        self.balance -= amount
        print(f"Со счета {self.currency_code} списано {amount:.4f}. Текущий баланс: {self.balance:.4f}")

    def withdraw(self, amount: float):
        """Снятие средств с баланса."""
        if not isinstance(amount, (int, float)) or amount <= 0:
            raise ValueError("Сумма снятия должна быть положительным числом.")
        if amount > self.balance:
            # Используем новое кастомное исключение
            raise InsufficientFundsError(available=self.balance, required=amount, code=self.currency_code)

        self.balance -= amount
    def get_balance_info(self) -> str:
        """Возвращает информацию о текущем балансе."""
        return f"Кошелек: {self.currency_code}, Баланс: {self.balance:.4f}"

    def to_dict(self) -> Dict:
        """Сериализация объекта в словарь."""
        return {"currency_code": self.currency_code, "balance": self.balance}

    @classmethod
    def from_dict(cls, data: Dict) -> 'Wallet':
        """Десериализация объекта из словаря."""
        return cls(currency_code=data['currency_code'], balance=data.get('balance', 0.0))


class Portfolio:
    """Управление всеми кошельками одного пользователя."""

    def __init__(self, user_id: int, wallets: Dict[str, Wallet] = None):
        self._user_id = user_id
        self._wallets = wallets if wallets else {}

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def wallets(self) -> Dict[str, Wallet]:
        """Возвращает копию словаря кошельков."""
        return self._wallets.copy()

    def add_currency(self, currency_code: str):
        """Добавляет новый кошелёк, если его ещё нет."""
        code = currency_code.upper()
        if code in self._wallets:
            raise ValueError(f"Кошелек для валюты {code} уже существует.")
        self._wallets[code] = Wallet(currency_code=code)
        print(f"Кошелек для {code} успешно добавлен.")

    def get_wallet(self, currency_code: str) -> Wallet:
        """Возвращает объект Wallet по коду валюты."""
        code = currency_code.upper()
        if code not in self._wallets:
            raise ValueError(f"Кошелек для валюты {code} не найден.")
        return self._wallets[code]

    def get_or_create_wallet(self, currency_code: str) -> Wallet:
        """Возвращает кошелек, создавая его при необходимости."""
        code = currency_code.upper()
        if code not in self._wallets:
            self._wallets[code] = Wallet(currency_code=code)
        return self._wallets[code]

    def get_total_value(self, base_currency: str, exchange_rates: Dict) -> float:
        """Возвращает общую стоимость всех валют в базовой валюте."""
        if not exchange_rates:
            exchange_rates = {
                "EUR_USD": {
                    "rate": 1.0786,
                    "updated_at": "2025-10-09T10:30:00"
                },
                "BTC_USD": {
                    "rate": 59337.21,
                    "updated_at": "2025-10-09T10:29:42"
                },
                "RUB_USD": {
                    "rate": 0.01016,
                    "updated_at": "2025-10-09T10:31:12"
                },
                "ETH_USD": {
                    "rate": 3720.00,
                    "updated_at": "2025-10-09T10:35:00"
                },
                "source": "ParserService",
                "last_refresh": "2025-10-09T10:35:00"
            }

        total_value = 0.0
        base_currency = base_currency.upper()

        for code, wallet in self._wallets.items():
            if code == base_currency:
                total_value += wallet.balance
            else:
                rate_key = f"{code}_{base_currency}"
                if rate_key not in exchange_rates:
                    # Попробуем найти обратный курс
                    reverse_rate_key = f"{base_currency}_{code}"
                    if reverse_rate_key in exchange_rates:
                        rate = 1 / exchange_rates[reverse_rate_key]['rate']
                    # rate = 1 / exchange_rates[reverse_rate_key]
                    else:
                        print(f"Предупреждение: курс для {rate_key} не найден, валюта не учитывается в общей сумме.")
                        continue
                else:
                    rate = exchange_rates[rate_key]['rate']
                # rate = exchange_rates[rate_key]

                total_value += wallet.balance * rate

        return total_value

    def to_dict(self) -> Dict:
        """Сериализация объекта в словарь."""
        return {
            "user_id": self._user_id,
            "wallets": {code: wallet.to_dict() for code, wallet in self._wallets.items()}
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Portfolio':
        """Десериализация объекта из словаря."""
        wallets = {code: Wallet.from_dict(w_data) for code, w_data in data.get('wallets', {}).items()}
        return cls(user_id=data['user_id'], wallets=wallets)
