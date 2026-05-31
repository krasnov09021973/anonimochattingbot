# services/limits_service.py
"""
Сервис для проверки и обновления лимитов.
"""

import logging
from datetime import datetime
from typing import Tuple

from repositories.user_repo import UserRepo
from config import settings
from lang import get_error

logger = logging.getLogger(__name__)

class LimitsService:
    def __init__(self, user_repo: UserRepo):
        self.user_repo = user_repo

    async def can_send_message(self, user_id: int) -> bool:
        """Проверяет, может ли пользователь отправить сообщение"""
        user = await self.user_repo.get_user_context(user_id)

        # Премиум — безлимит
        if user.get('is_premium_user'):
            return True

        # Проверка бана
        if user.get('is_banned'):
            return False

        # Проверка дневного лимита
        # TODO: реализовать учёт дневных сообщений
        return True

    async def get_daily_limit(self, user_id: int) -> Tuple[int, int, bool]:
        """
        Возвращает (лимит, использовано, превышен_ли_лимит)
        """
        # TODO: реализовать
        return settings.daily_limit_user, 0, False
