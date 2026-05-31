# config.py
"""
Конфигурация бота с использованием pydantic-settings.
Все настройки загружаются из .env файла и проверяются на типы.
"""

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Настройки бота"""

    # ========== Telegram ==========
    bot_token: str                                    # Токен бота из BotFather

    # ========== AI ==========
    ai_enabled: bool = True                           # Включить AI-собеседника
    ai_timeout: int = 15                              # Таймаут до подключения AI (секунды)
    ai_api_key: str = ""                              # API ключ для AI (OpenRouter)
    ai_api_url: str = ""                              # URL для AI (OpenRouter)
    max_free_ai_messages: int = 50                    # Лимит сообщений для бесплатных пользователей

    # ========== Администраторы ==========
    admin_ids: List[int] = []                         # Telegram ID админов

    # ========== Пути ==========
    base_dir: Path = Path(__file__).parent
    db_path: Path = base_dir / "data" / "anon_chat.db"
    log_dir: Path = base_dir / "logs"

    # ========== Лимиты ==========
    daily_limit_guest: int = 5                        # Гость (до 60 чатов)
    daily_limit_user: int = 10                        # Обычный пользователь
    daily_limit_trusted: int = 15                     # Репутация 50-79
    daily_limit_vip: int = 999                        # Премиум / репутация 80+

    # ========== Возрастные ограничения ==========
    min_age: int = 12
    max_age: int = 99

    # ========== Премиум (цены) ==========
    vip_price_week: int = 199
    vip_price_month: int = 499
    vip_price_3months: int = 1499
    vip_price_year: int = 1899

    class Config:
        # .env на уровень выше (в корне проекта)
        env_file = Path(__file__).parent.parent / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Игнорируем лишние переменные в .env


# Создаём глобальный экземпляр настроек
settings = Settings()

# Создаём необходимые папки
settings.log_dir.mkdir(parents=True, exist_ok=True)
settings.db_path.parent.mkdir(parents=True, exist_ok=True)
