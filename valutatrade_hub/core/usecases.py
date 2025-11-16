from typing import List, Dict, Tuple
from .models import User, Portfolio
from .utils import (
    load_data, save_data, USERS_FILE, PORTFOLIOS_FILE, RATES_FILE,
    get_current_user_id, set_current_user, logout_user as util_logout
)

def register_user(username: str, password: str) -> User:
    """Регистрирует нового пользователя."""
    users_data = load_data(USERS_FILE)

    if any(u['username'] == username for u in users_data):
        raise ValueError(f"Имя пользователя '{username}' уже занято")

    new_user_id = max([u['user_id'] for u in users_data] + [0]) + 1

    new_user = User(user_id=new_user_id, username=username, password=password)
    users_data.append(new_user.to_dict())
    save_data(USERS_FILE, users_data)

    portfolios_data = load_data(PORTFOLIOS_FILE)
    new_portfolio = Portfolio(user_id=new_user_id)

    usd_wallet = new_portfolio.get_or_create_wallet("USD")
    usd_wallet.balance = 10000.0
    portfolios_data.append(new_portfolio.to_dict())
    save_data(PORTFOLIOS_FILE, portfolios_data)

    return new_user


def login_user(username: str, password: str) -> User:
    """Аутентифицирует пользователя и создает сессию."""
    users_data = load_data(USERS_FILE)
    user_data = next((u for u in users_data if u['username'] == username), None)

    if not user_data:
        raise ValueError(f"Пользователь '{username}' не найден")

    user = User.from_dict(user_data)

    if not user.verify_password(password):
        raise ValueError("Неверный пароль")

    set_current_user(user.user_id)
    return user


def get_logged_in_user() -> User | None:
    """Возвращает объект текущего залогиненного пользователя."""
    user_id = get_current_user_id()
    if user_id is None:
        return None

    users_data = load_data(USERS_FILE)
    user_data = next((u for u in users_data if u['user_id'] == user_id), None)

    if user_data:
        return User.from_dict(user_data)
    return None


def logout():
    """Завершает сессию пользователя."""
    util_logout()


# --- Управление портфелем ---

def get_user_portfolio(user: User) -> Portfolio:
    """Загружает портфель для указанного пользователя."""
    portfolios_data = load_data(PORTFOLIOS_FILE)
    portfolio_data = next((p for p in portfolios_data if p['user_id'] == user.user_id), None)

    if not portfolio_data:
        raise FileNotFoundError(f"Портфель для пользователя {user.username} не найден.")

    return Portfolio.from_dict(portfolio_data)


def save_user_portfolio(portfolio: Portfolio):
    """Сохраняет обновленный портфель пользователя."""
    portfolios_data = load_data(PORTFOLIOS_FILE)

    portfolios_data = [p for p in portfolios_data if p['user_id'] != portfolio.user_id]
    portfolios_data.append(portfolio.to_dict())
    save_data(PORTFOLIOS_FILE, portfolios_data)


def get_exchange_rate(from_currency: str, to_currency: str) -> Tuple[float, str]:
    """Получает курс обмена из кеша."""
    rates_data = load_data(RATES_FILE)
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
        return 1 / rate_info['rate'], rate_info['updated_at']

    rate_from_usd_key = f"{from_currency}_USD"
    rate_to_usd_key = f"{to_currency}_USD"

    if rate_from_usd_key in rates_data and rate_to_usd_key in rates_data:
        rate_from = rates_data[rate_from_usd_key]['rate']
        rate_to = rates_data[rate_to_usd_key]['rate']
        if rate_to == 0:
            raise ValueError("Нулевой курс, деление невозможно.")
        cross_rate = rate_from / rate_to

        updated_at = max(rates_data[rate_from_usd_key]['updated_at'], rates_data[rate_to_usd_key]['updated_at'])
        return cross_rate, updated_at

    raise ValueError(f"Не удалось получить курс для {from_currency}→{to_currency}")


def buy_currency(user: User, currency: str, amount: float, base_currency: str = "USD"):
    """Покупка валюты за базовую валюту (USD)."""
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    currency = currency.upper()
    if currency == base_currency:
        raise ValueError(f"Нельзя купить базовую валюту '{base_currency}' саму за себя.")

    portfolio = get_user_portfolio(user)
    rate, _ = get_exchange_rate(currency, base_currency)

    cost = amount * rate

    base_wallet = portfolio.get_or_create_wallet(base_currency)

    if base_wallet.balance < cost:
        raise ValueError(
            f"Недостаточно средств: требуется {cost:.2f} {base_currency}, доступно {base_wallet.balance:.2f} {base_currency}")

    target_wallet = portfolio.get_or_create_wallet(currency)
    old_target_balance = target_wallet.balance

    base_wallet.withdraw(cost)
    target_wallet.deposit(amount)

    save_user_portfolio(portfolio)

    return {
        "amount": amount,
        "currency": currency,
        "rate": rate,
        "cost": cost,
        "base_currency": base_currency,
        "old_balance": old_target_balance,
        "new_balance": target_wallet.balance
    }


def sell_currency(user: User, currency: str, amount: float, base_currency: str = "USD"):
    """Продажа валюты за базовую валюту (USD)."""
    if amount <= 0:
        raise ValueError("'amount' должен быть положительным числом")

    currency = currency.upper()
    if currency == base_currency:
        raise ValueError(f"Нельзя продать базовую валюту '{base_currency}'.")

    portfolio = get_user_portfolio(user)
    target_wallet = portfolio.get_wallet(currency)  # Здесь ошибка если кошелька нет

    if target_wallet.balance < amount:
        raise ValueError(
            f"Недостаточно средств: доступно {target_wallet.balance:.4f} {currency}, требуется {amount:.4f} {currency}")

    rate, _ = get_exchange_rate(currency, base_currency)
    revenue = amount * rate

    old_target_balance = target_wallet.balance

    target_wallet.withdraw(amount)
    base_wallet = portfolio.get_or_create_wallet(base_currency)
    base_wallet.deposit(revenue)

    save_user_portfolio(portfolio)

    return {
        "amount": amount,
        "currency": currency,
        "rate": rate,
        "revenue": revenue,
        "base_currency": base_currency,
        "old_balance": old_target_balance,
        "new_balance": target_wallet.balance
    }
