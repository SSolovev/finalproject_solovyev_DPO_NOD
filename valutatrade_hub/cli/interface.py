import click

from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    BaseTradeError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.infra.database import db_manager
from valutatrade_hub.parser_service.updater import get_default_updater

from ..core import usecases
from ..core.utils import RATES_FILE, load_data


@click.group()
def cli():
    """
    Платформа для отслеживания и симуляции торговли валютами.
    """
    pass


@cli.command()
@click.option('--username', required=True,
              prompt="Имя пользователя", help="Имя нового пользователя.")
@click.option('--password', required=True, prompt=True,
              hide_input=True, confirmation_prompt=True,
              help="Пароль (минимум 4 символа).")
def register(username, password):
    """Создать нового пользователя."""
    try:
        if len(password) < 4:
            click.echo("Ошибка: Пароль должен быть "
                       "не короче 4 символов", err=True)
            return
        user = usecases.register_user(username, password)
        click.echo(f"Пользователь '{user.username}' зарегистрирован "
                   f"(id={user.user_id}).")
        click.echo("Вам начислен стартовый капитал 10000 USD.")
        click.echo(f"Войдите: trade login --username {user.username} --password ****")
    except ValueError as e:
        click.echo(f"Ошибка: {e}", err=True)


@cli.command()
@click.option('--username', required=True, prompt="Имя пользователя",
              help="Имя пользователя для входа.")
@click.option('--password', required=True, prompt="Пароль", hide_input=True,
              help="Пароль пользователя.")
def login(username, password):
    """Войти в систему."""
    try:
        user = usecases.login_user(username, password)
        click.echo(f"Вы вошли как '{user.username}'")
    except ValueError as e:
        click.echo(f"Ошибка: {e}", err=True)


@cli.command()
def logout():
    """Выйти из системы."""
    usecases.logout()
    click.echo("Вы вышли из системы.")


@cli.command('show-portfolio')
@click.option('--base', default='USD', help="Базовая валюта "
                                            "для отображения общей стоимости.")
def show_portfolio(base):
    """Показать портфель текущего пользователя."""
    user = usecases.get_logged_in_user()
    if not user:
        click.echo("Ошибка: Сначала выполните login", err=True)
        return

    try:
        portfolio = usecases.get_user_portfolio(user)
        rates = load_data(RATES_FILE)

        base = base.upper()
        if base != 'USD' and f"{base}_USD" not in rates:
            click.echo(f"Ошибка: Неизвестная базовая валюта '{base}'", err=True)
            return

        click.echo(f"Портфель пользователя '{user.username}' (база: {base}):")

        if not portfolio.wallets:
            click.echo("Ваш портфель пуст.")
            return

        total_value = 0
        for code, wallet in sorted(portfolio.wallets.items()):
            value_in_base = wallet.balance
            if code != base:
                try:
                    rate, _ = usecases.get_exchange_rate(code, base)
                    value_in_base *= rate
                except ValueError:
                    value_in_base = 0  # Не можем посчитать

            total_value += value_in_base
            click.echo(f"- {code}: {wallet.balance:<10.4f} → "
                       f"{value_in_base:10.2f} {base}")

        click.echo("---------------------------------")
        click.echo(f"ИТОГО: {total_value:13.2f} {base}")

    except Exception as e:
        click.echo(f"Ошибка: {e}", err=True)


@cli.command()
@click.option('--currency', required=True,
              help="Код покупаемой валюты (например, BTC).")
@click.option('--amount', required=True, type=float,
              help="Количество покупаемой валюты.")
def buy(currency, amount):
    """Купить валюту."""
    user = usecases.get_logged_in_user()
    if not user:
        click.echo("Ошибка: Сначала выполните login.", err=True)
        return

    try:
        result = usecases.buy_currency(user=user, currency=currency,
                                       amount=amount)
        click.echo(f"Покупка выполнена: {result['amount']:.4f} "
                   f"{result['currency']}")
        click.echo(f"Оценочная стоимость: {result['cost']:.2f} "
                   f"{result['base_currency']}")
    except (InsufficientFundsError, CurrencyNotFoundError,
            ApiRequestError, ValueError) as e:
        click.echo(f"Ошибка покупки: {e}", err=True)
        if isinstance(e, CurrencyNotFoundError):
            click.echo("Совет: используйте команду 'list-currencies' "
                       "для просмотра доступных валют.")
        if isinstance(e, ApiRequestError):
            click.echo("Совет: проверьте сетевое подключение или "
                       "обновите кеш курсов (если есть команда).")


@cli.command()
@click.option('--currency', required=True,
              help="Код продаваемой валюты.")
@click.option('--amount', required=True, type=float,
              help="Количество продаваемой валюты.")
def sell(currency, amount):
    """Продать валюту."""
    user = usecases.get_logged_in_user()
    if not user:
        click.echo("Ошибка: Сначала выполните login.", err=True)
        return

    try:
        result = usecases.sell_currency(user=user, currency=currency, amount=amount)
        click.echo(f"Продажа выполнена: {result['amount']:.4f} "
                   f"{result['currency']}")
        click.echo(f"Оценочная выручка: {result['revenue']:.2f} "
                   f"{result['base_currency']}")
    except ValueError as e:
        # Отдельно обрабатываем ошибку отсутствия кошелька
        if "кошелек" in str(e).lower() and "не найден" in str(e).lower():
            click.echo(f"Ошибка: У вас нет кошелька '{currency.upper()}'. "
                       f"Он создаётся при первой покупке.", err=True)
        else:
            click.echo(f"Ошибка продажи: {e}", err=True)
    except (InsufficientFundsError, CurrencyNotFoundError, ApiRequestError) as e:
        click.echo(f"Ошибка продажи: {e}", err=True)


@cli.command('get-rate')
@click.option('--from', 'from_curr', required=True, help="Исходная валюта.")
@click.option('--to', 'to_curr', required=True, help="Целевая валюта.")
def get_rate(from_curr, to_curr):
    """Получить текущий курс одной валюты к другой."""
    try:
        if not from_curr.strip() or not to_curr.strip():
            raise ValueError("Коды валют не могут быть пустыми.")

        rate, updated_at = usecases.get_exchange_rate(from_curr, to_curr)
        click.echo(f"Курс: 1 {from_curr.upper()} = {rate:.6f} {to_curr.upper()} "
                   f"(Данные на: {updated_at})")
    except (ValueError, CurrencyNotFoundError, ApiRequestError) as e:
        click.echo(f"Ошибка: {e}", err=True)
        if isinstance(e, CurrencyNotFoundError):
            click.echo("Совет: используйте команду 'list-currencies' "
                       "для просмотра доступных валют.")


@cli.command()
def list_currencies():
    """Показать список всех поддерживаемых валют."""
    click.echo("Поддерживаемые валюты:")
    supported_codes = ["USD", "EUR", "RUB", "BTC", "ETH"]
    for code in supported_codes:
        try:
            currency_obj = usecases.get_currency_info(code)
            click.echo(f"- {currency_obj.get_display_info()}")
        except CurrencyNotFoundError:
            continue


@cli.command('update-rates')
@click.option('--source',
              type=click.Choice(['coingecko', 'exchangerate'],
                                case_sensitive=False),
              help="Обновить данные только из указанного источника.")
def update_rates(source):
    """Запустить немедленное обновление курсов валют."""
    try:
        updater = get_default_updater()
        updater.run_update(source_filter=source)
        click.echo("Обновление курсов завершено. Проверьте лог-файл для деталей.")
    except BaseTradeError as e:
        click.echo(f"Ошибка при обновлении: {e}", err=True)
    except Exception as e:
        click.echo(f"Непредвиденная ошибка: {e}", err=True)


@cli.command('show-rates')
@click.option('--currency', help="Показать курс только для"
                                 " указанной валюты (например, BTC).")
@click.option('--top', type=int, help="Показать N самых дорогих"
                                      " криптовалют.")
@click.option('--base', default='USD', help="Показать курсы относительно"
                                            " указанной базы.")
def show_rates(currency, top, base):
    """Показать актуальные курсы из локального кеша."""
    try:
        rates_data = db_manager.load_rates()
        if not rates_data or not rates_data.get("pairs"):
            click.echo("Локальный кеш курсов пуст. "
                       "Выполните 'trade update-rates'.", err=True)
            return

        click.echo(f"Курсы из кеша "
                   f"(обновлено: {rates_data.get('last_refresh', 'N/A')})")

        all_pairs = rates_data["pairs"]
        output_rates = []

        for pair_key, data in all_pairs.items():
            from_c, to_c = pair_key.split('_')

            if to_c == base.upper():
                rate = data['rate']

            else:
                continue

            if currency and from_c != currency.upper():
                continue

            output_rates.append((pair_key, rate))

        if top:
            output_rates.sort(key=lambda x: x[1], reverse=True)
            output_rates = output_rates[:top]
        else:
            output_rates.sort()

        if not output_rates:
            click.echo(f"Курсы для '{currency or base}' не найдены в кеше.")
            return

        for pair_key, rate in output_rates:
            click.echo(f"- {pair_key}: {rate:.6f}")

    except Exception as e:
        click.echo(f"Ошибка при чтении кеша: {e}", err=True)


if __name__ == '__main__':
    cli()
