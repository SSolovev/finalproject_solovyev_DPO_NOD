# ValutaTrade Hub

Это комплексная платформа для симуляции торговли фиатными и криптовалютами.

## Структура проекта

- `data/`: JSON-файлы для хранения данных (пользователи, портфели, курсы).
- `valutatrade_hub/`: Основной исходный код приложения.
  - `core/`: Бизнес-логика, модели данных.
  - `cli/`: Командный интерфейс.
- `main.py`: Точка входа для запуска CLI.

## Установка и запуск

Для работы проекта требуется Python 3.9+ и Poetry.

1.  **Установите зависимости:**
    ```bash
    poetry install
    ```

2.  **Запустите приложение:**
    Все команды выполняются через `poetry run`. Вместо `trade` можно использовать `python main.py`.

    ```bash
    poetry run trade --help
    ```

## Основные команды

- `register`: Регистрация нового пользователя.
- `login`: Вход в систему.
- `logout`: Выход из системы.
- `show-portfolio`: Показать текущий портфель и балансы.
- `buy`: Купить валюту.
- `sell`: Продать валюту.
- `get-rate`: Получить курс обмена между двумя валютами.

### Примеры использования

```bash
# Регистрация
poetry run trade register --username alice --password mysecretpassword

# Вход
poetry run trade login --username alice --password mysecretpassword

# Просмотр портфеля
poetry run trade show-portfolio

# Покупка Bitcoin
poetry run trade buy --currency BTC --amount 0.05

# Продажа Ethereum
poetry run trade sell --currency ETH --amount 1.5

# Получение курса
poetry run trade get-rate --from BTC --to EUR

#### 12. `Makefile`
Простой Makefile для удобства.

install:
	@echo ">>> Installing dependencies using Poetry..."
	poetry install

run:
	@echo ">>> Running CLI application. Use 'poetry run trade --help' for commands."
	poetry run trade

help:
	@echo "Available commands:"
	@echo "  make install    - Install project dependencies"
	@echo "  make run        - Run the CLI application (shows help)"
	poetry run trade --help