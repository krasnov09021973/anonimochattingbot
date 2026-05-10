# services/limits_service.py
"""
Сервис для управления дневными лимитами пользователей.

Что делает:
1. Отслеживание количества чатов пользователя за день
2. Автоматический сброс лимитов в 00:00 UTC
3. Очистка старых записей из БД
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional

from repositories.user_repo import UserRepo

logger = logging.getLogger(__name__)


class LimitsService:
    """Сервис для управления дневными лимитами"""

    def __init__(self, user_repo: UserRepo):
        """
        Инициализация сервиса лимитов.

        :param user_repo: репозиторий пользователей
        """
        self.user_repo = user_repo
        self._ensure_table()

    def _ensure_table(self):
        """Создаёт таблицу для дневной статистики, если её нет"""
        # TODO: добавить создание таблицы user_daily_stats
        # Пока заглушка
        pass

    # ================================================================
    # РАБОТА С ДНЕВНЫМИ ЛИМИТАМИ
    # ================================================================

    def get_today_stats(self, user_id: int) -> Dict:
        """
        Возвращает статистику пользователя за сегодня.

        :return: {'chats_count': int, 'messages_count': int, 'date': str}
        """
        # TODO: реализовать получение из БД
        return {'chats_count': 0, 'messages_count': 0, 'date': datetime.utcnow().strftime('%Y-%m-%d')}

    def increment_chats_today(self, user_id: int) -> bool:
        """
        Увеличивает счётчик чатов пользователя за сегодня.
        """
        # Премиум не учитываем
        if self.user_repo.is_premium(user_id):
            return True

        today = datetime.utcnow().strftime('%Y-%m-%d')
        # TODO: INSERT OR UPDATE в таблицу user_daily_stats
        return True

    def get_remaining_chats(self, user_id: int, daily_limit: int) -> int:
        """
        Возвращает количество оставшихся чатов на сегодня.
        """
        stats = self.get_today_stats(user_id)
        used = stats.get('chats_count', 0)
        return max(0, daily_limit - used)

    # ================================================================
    # ФОНОВАЯ ЗАДАЧА ДЛЯ СБРОСА ЛИМИТОВ
    # ================================================================

    async def start_reset_scheduler(self):
        """
        Запускает фоновую задачу для сброса лимитов каждый день в 00:00 UTC.
        Добавить вызов в main.py: asyncio.create_task(limits_service.start_reset_scheduler())
        """
        while True:
            now = datetime.utcnow()
            # Следующий сброс в 00:00 UTC
            next_reset = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            wait_seconds = (next_reset - now).total_seconds()

            logger.info(f"[LIMITS] Следующий сброс через {wait_seconds / 3600:.1f} часов")
            await asyncio.sleep(wait_seconds)

            await self._reset_limits()

    async def _reset_limits(self):
        """
        Сбрасывает дневные лимиты (очищает старые записи).
        """
        try:
            # Удаляем записи старше 7 дней
            # TODO: реализовать DELETE FROM user_daily_stats WHERE date < date('now', '-7 days')
            logger.info("[LIMITS] Очистка старых записей выполнена")
        except Exception as e:
            logger.error(f"[LIMITS] Ошибка при сбросе: {e}")
