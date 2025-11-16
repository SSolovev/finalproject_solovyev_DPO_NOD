# valutatrade_hub/infra/settings.py
import toml
from typing import Any

class SettingsLoader:
    """
    Singleton для загрузки и предоставления доступа к конфигурации проекта.
    Конфигурация загружается из секции [tool.valutatrade] в pyproject.toml.

    Реализован через переопределение __new__ для простоты и наглядности.
    Это гарантирует, что при каждом импорте и вызове будет возвращаться
    один и тот же экземпляр класса, избегая повторной загрузки конфига.
    """
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsLoader, cls).__new__(cls)
            cls._instance.reload()
        return cls._instance

    def reload(self):
        """Загружает или перезагружает конфигурацию из файла."""
        try:
            with open('pyproject.toml', 'r', encoding='utf-8') as f:
                pyproject_data = toml.load(f)
                self._config = pyproject_data.get('tool', {}).get('valutatrade', {})
        except FileNotFoundError:
            print("Warning: pyproject.toml не найден. Используются значения по умолчанию.")
            self._config = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Получает значение из конфигурации по ключу."""
        return self._config.get(key, default)


settings = SettingsLoader()