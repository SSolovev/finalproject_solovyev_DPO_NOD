import click
from ..core import usecases
from ..core.utils import RATES_FILE, load_data


@click.group()
def cli():
    """
    Платформа для отслеживания и симуляции торговли валютами.
    """
    pass


@cli.command()
@click.option('--username', required=True, prompt="Имя пользователя", help="Имя нового пользователя.")
@click.option('--password', required=True, prompt=True, hide_input=True, confirmation_prompt=True,
              help="Пароль (минимум 4 символа).")
def register(username, password):
    """Создать нового пользователя."""
    try:
        if len(password) < 4:
            click.echo("Ошибка: Пароль должен быть не короче 4 символов", err=True)
            return
        user = usecases.register_user(username, password)
        click.echo(f"Пользователь '{user.username}' зарегистрирован (id={user.user_id}).")
        click.echo(f"Вам начислен стартовый капитал 10000 USD.")
        click.echo(f"Войдите: trade login --username {user.username} --password ****")
    except ValueError as e:
        click.echo(f"Ошибка: {e}", err=True)


@cli.command()
@click.option('--username', required=True, prompt="Имя пользователя", help="Имя пользователя для входа.")
@click.option('--password', required=True, prompt="Пароль", hide_input=True, help="Пароль пользователя.")
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
@click.option('--base', default='USD', help="Базовая валюта для отображения общей стоимости.")
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
            click.echo(f"- {code}: {wallet.balance:<10.4f} → {value_in_base:10.2f} {base}")

        click.echo("---------------------------------")
        click.echo(f"ИТОГО: {total_value:13.2f} {base}")

    except Exception as e:
        click.echo(f"Ошибка: {e}", err=True)


@cli.command()
@click.option('--currency', required=True, help="Код покупаемой валюты (например, BTC).")
@click.option('--amount', required=True, type=float, help="Количество покупаемой валюты.")
def buy(currency, amount):
    """Купить валюту за USD."""
    user = usecases.get_logged_in_user()
    if not user:
        click.echo("Ошибка: Сначала выполните login", err=True)
        return

    try:
        result = usecases.buy_currency(user, currency, amount)
        click.echo(
            f"Покупка выполнена: {result['amount']:.4f} {result['currency']} по курсу {result['rate']:.2f} {result['base_currency']}/{result['currency']}")
        click.echo(f"Оценочная стоимость покупки: {result['cost']:.2f} {result['base_currency']}")
        click.echo("Изменения в портфеле:")
        click.echo(f"- {result['currency']}: было {result['old_balance']:.4f} → стало {result['new_balance']:.4f}")
    except ValueError as e:
        click.echo(f"Ошибка: {e}", err=True)


@cli.command()
@click.option('--currency', required=True, help="Код продаваемой валюты.")
@click.option('--amount', required=True, type=float, help="Количество продаваемой валюты.")
def sell(currency, amount):
    """Продать валюту и получить USD."""
    user = usecases.get_logged_in_user()
    if not user:
        click.echo("Ошибка: Сначала выполните login", err=True)
        return

    try:
        result = usecases.sell_currency(user, currency, amount)
        click.echo(
            f"Продажа выполнена: {result['amount']:.4f} {result['currency']} по курсу {result['rate']:.2f} {result['base_currency']}/{result['currency']}")
        click.echo(f"Оценочная выручка: {result['revenue']:.2f} {result['base_currency']}")
        click.echo("Изменения в портфеле:")
        click.echo(f"- {result['currency']}: было {result['old_balance']:.4f} → стало {result['new_balance']:.4f}")
    except ValueError as e:
        if "не найден" in str(e).lower():
            click.echo(
                f"Ошибка: У вас нет кошелька '{currency.upper()}'. Он создаётся автоматически при первой покупке.",
                err=True)
        else:
            click.echo(f"Ошибка: {e}", err=True)


@cli.command('get-rate')
@click.option('--from', 'from_curr', required=True, help="Исходная валюта.")
@click.option('--to', 'to_curr', required=True, help="Целевая валюта.")
def get_rate(from_curr, to_curr):
    """Получить текущий курс одной валюты к другой."""
    try:
        if not from_curr.strip() or not to_curr.strip():
            raise ValueError("Коды валют не могут быть пустыми.")

        rate, updated_at = usecases.get_exchange_rate(from_curr, to_curr)
        click.echo(f"Курс: 1 {from_curr.upper()} = {rate:.6f} {to_curr.upper()}")
        click.echo(f"Данные на: {updated_at}")
    except ValueError as e:
        click.echo(f"Ошибка: {e}", err=True)


if __name__ == '__main__':
    cli()
