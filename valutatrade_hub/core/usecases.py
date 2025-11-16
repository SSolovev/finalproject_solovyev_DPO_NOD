# valutatrade_hub/core/usecases.py
from datetime import datetime, timedelta
from typing import Tuple

from .models import User, Portfolio
from .currencies import get_currency, Currency
from .exceptions import ApiRequestError, CurrencyNotFoundError, InsufficientFundsError
from ..infra.database import db_manager
from ..infra.settings import settings
from ..decorators import log_action


# --- Управление пользователями и сессией ---

@log_action("REGISTER")
def register_user(username: str, password: str) -> User:
    users_data = db_manager.load_users()

    if any(u['username'] == username for u in users_data):
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    new_user_id = max([u['user_id'] for u in users_data] + [0]) + 1
    new_user = User(user_id=new_user_id, username=username, password=password)
    users_data.append(new_user.to_dict())
    db_manager.save_users(users_data)

    portfolios_data = db_manager.load_portfolios()
    new_portfolio = Portfolio(user_id=new_user_id)
    usd_wallet = new_portfolio.get_or_create_wallet("USD")
    usd_wallet.balance = 10000.0
    portfolios_data.append(new_portfolio.to_dict())
    db_manager.save_portfolios(portfolios_data)

    return new_user


@log_action("LOGIN")
def login_user(username: str, password: str) -> User:
    users_data = db_manager.load_users()
    user_data = next((u for u in users_data if u['username'] == username), None)

    if not user_data:
        raise ValueError(f"Пользователь '{username}' не найден")

    user = User.from_dict(user_data)
    if not user.verify_password(password):
        raise ValueError("Неверный пароль")

    db_manager.set_current_user(user.user_id)
    return user


def get_logged_in_user() -> User | None:
    user_id = db_manager.get_current_user_id()
    if user_id is None:
        return None

    users_data = db_manager.load_users()
    user_data = next((u for u in users_data if u['user_id'] == user_id), None)

    return User.from_dict(user_data) if user_data else None


def logout():
    db_manager.logout_user()


# --- Управление портфелем ---

def get_user_portfolio(user: User) -> Portfolio:
    portfolios_data = db_manager.load_portfolios()
    portfolio_data = next((p for p in portfolios_data if p['user_id'] == user.user_id), None)
    if not portfolio_data:
        raise FileNotFoundError(f"Портфель для пользователя {user.username} не найден.")
    return Portfolio.from_dict(portfolio_data)


def save_user_portfolio(portfolio: Portfolio):
    portfolios_data = db_manager.load_portfolios()
    portfolios_data = [p for p in portfolios_data if p['user_id'] != portfolio.user_id]
    portfolios_data.append(portfolio.to_dict())
    db_manager.save_portfolios(portfolios_data)


def get_currency_info(code: str) -> Currency:
    return get_currency(code)


def get_exchange_rate(from_currency: str, to_currency: str) -> Tuple[float, str]:
    rates_data = db_manager.load_rates()
    ttl = settings.get("rates_ttl_seconds", 300)

    last_refresh_str = rates_data.get("last_refresh", "2025-11-16T20:10:00")
    last_refresh_dt = datetime.fromisoformat(last_refresh_str)

    if datetime.now() - last_refresh_dt > timedelta(seconds=ttl):
        raise ApiRequestError(f"Кеш курсов устарел (старше {ttl} секунд). Запустите сервис парсинга.")

    from_currency, to_currency = from_currency.upper(), to_currency.upper()

    if from_currency == to_currency:
        return 1.0, rates_data.get('last_refresh', 'N/A')

    rate_key = f"{from_currency}_{to_currency}"
    if rate_key in rates_data:
        rate_info = rates_data[rate_key]
        return rate_info['rate'], rate_info['updated_at']

    reverse_rate_key = f"{to_currency}_{from_currency}"
    if reverse_rate_key in rates_data:
        rate_info = rates_data[reverse_rate_key]
        if rate_info['rate'] == 0: raise ValueError("Нулевой курс, деление невозможно.")
        return 1 / rate_info['rate'], rate_info['updated_at']

    raise ValueError(f"Не удалось найти прямой или обратный курс для {from_currency}→{to_currency}")


@log_action("BUY", verbose=True)
def buy_currency(user: User, currency: str, amount: float):
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    get_currency(currency)  # Валидация существования валюты
    base_currency = settings.get("default_base_currency", "USD")

    if currency.upper() == base_currency:
        raise ValueError(f"Нельзя купить базовую валюту '{base_currency}' саму за себя.")

    portfolio = get_user_portfolio(user)
    rate, _ = get_exchange_rate(currency, base_currency)
    cost = amount * rate

    base_wallet = portfolio.get_or_create_wallet(base_currency)
    target_wallet = portfolio.get_or_create_wallet(currency)
    old_target_balance = target_wallet.balance

    base_wallet.withdraw(cost)  # Может выбросить InsufficientFundsError
    target_wallet.deposit(amount)

    save_user_portfolio(portfolio)

    return {
        "amount": amount, "currency": currency.upper(), "rate": rate,
        "cost": cost, "base_currency": base_currency, "old_balance": old_target_balance,
        "new_balance": target_wallet.balance, "user": user
    }


@log_action("SELL", verbose=True)
def sell_currency(user: User, currency: str, amount: float):
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    get_currency(currency)  # Валидация существования валюты
    base_currency = settings.get("default_base_currency", "USD")

    if currency.upper() == base_currency:
        raise ValueError(f"Нельзя продать базовую валюту '{base_currency}'.")

    portfolio = get_user_portfolio(user)
    target_wallet = portfolio.get_wallet(currency)  # Может выбросить ValueError если кошелька нет
    old_target_balance = target_wallet.balance

    rate, _ = get_exchange_rate(currency, base_currency)
    revenue = amount * rate

    target_wallet.withdraw(amount)  # Может выбросить InsufficientFundsError
    base_wallet = portfolio.get_or_create_wallet(base_currency)
    base_wallet.deposit(revenue)

    save_user_portfolio(portfolio)

    return {
        "amount": amount, "currency": currency.upper(), "rate": rate,
        "revenue": revenue, "base_currency": base_currency, "old_balance": old_target_balance,
        "new_balance": target_wallet.balance, "user": user
    }