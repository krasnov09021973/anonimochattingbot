# services/rating_service.py
"""
Сервис для обработки оценок пользователей (рейтинга).

Что делает:
1. Обработка оценок после завершения чата (👍/👎)
2. Изменение репутации пользователей
3. Защита от повторных оценок в одном чате
4. Сохранение оценок в БД
"""

import logging
from typing import Tuple, Optional

from repositories.universe import Universe
from repositories.user_repo import UserRepo
from repositories.chat_repo import ChatRepo

logger = logging.getLogger(__name__)


class RatingService:
    """Сервис для работы с оценками и репутацией"""

    # Дельта изменения репутации
    REP_GOOD = 5   # положительная оценка
    REP_BAD = -5   # отрицательная оценка

    def __init__(self, universe: Universe, user_repo: UserRepo, chat_repo: ChatRepo):
        """
        Инициализация сервиса оценок.

        :param universe: единое хранилище состояний
        :param user_repo: репозиторий пользователей
        :param chat_repo: репозиторий чатов
        """
        self.universe = universe
        self.user_repo = user_repo
        self.chat_repo = chat_repo

    # ================================================================
    # ОСНОВНЫЕ МЕТОДЫ
    # ================================================================

    async def process_rating(self, rater_id: int, rated_id: int, rating: str, chat_token: str) -> Tuple[bool, str]:
        """
        Обрабатывает оценку пользователя.

        :param rater_id: ID того, кто оценивает
        :param rated_id: ID того, кого оценивают
        :param rating: 'good' или 'bad'
        :param chat_token: токен чата (для проверки повторных оценок)
        :return: (успех, сообщение)
        """
        # 1. Проверяем, не AI ли это (AI не оценивают)
        if rated_id == 0:
            logger.info(f"Попытка оценить AI от {rater_id}")
            return False, "🤖 AI-собеседников не оценивают"

        # 2. Проверяем, не оценивает ли пользователь сам себя
        if rater_id == rated_id:
            logger.warning(f"Пользователь {rater_id} пытался оценить себя")
            return False, "❌ Нельзя оценить самого себя"

        # 3. Проверяем, не оценивал ли уже в этом чате
        if self.chat_repo.has_rated(rater_id, rated_id, chat_token):
            logger.info(f"Повторная оценка от {rater_id} на {rated_id} в чате {chat_token}")
            return False, "❌ Вы уже оценили собеседника в этом чате"

        # 4. Изменяем репутацию
        delta = self.REP_GOOD if rating == 'good' else self.REP_BAD
        success, new_rep, msg = self.user_repo.change_reputation(
            rated_id,
            delta,
            reason=f"Оценка от {rater_id}: {rating}"
        )

        if not success:
            logger.error(f"Ошибка изменения репутации: {msg}")
            return False, "❌ Ошибка при изменении репутации"

        # 5. Сохраняем оценку в БД
        self.chat_repo.add_rating(rater_id, rated_id, rating, chat_token)

        # 6. Возвращаем сообщение пользователю
        user_message = self._get_rating_message(rating, new_rep, delta)

        logger.info(f"Оценка {rating} от {rater_id} -> {rated_id}, репутация: {new_rep}")
        return True, user_message

    def _get_rating_message(self, rating: str, new_rep: int, delta: int) -> str:
        """
        Формирует сообщение для пользователя после оценки.
        """
        if rating == 'good':
            return f"✅ Оценка засчитана!"
        else:
            return f"👎 Оценка засчитана!"

    # ================================================================
    # РЕПУТАЦИЯ
    # ================================================================

    def get_reputation(self, user_id: int) -> int:
        """
        Возвращает репутацию пользователя.
        """
        return self.user_repo.get_reputation(user_id)

    def get_reputation_level(self, user_id: int) -> dict:
        """
        Возвращает уровень репутации и соответствующие бонусы.

        Уровни:
        - Забанен (≤0) — 0 чатов/день
        - Ограничен (1-9) — 1 чат/день
        - Предупреждение (10-24) — 5 чатов/день
        - Обычный (25-49) — 10 чатов/день
        - Надёжный (50-79) — 15 чатов/день
        - Высокая (80-100) — безлимит
        """
        rep = self.get_reputation(user_id)
        user_data = self.user_repo.get_user(user_id)
        chats_count = user_data.get('total_chats', 0) if user_data else 0

        from config import ADMIN_IDS

        # Админ — абсолютный приоритет
        if str(user_id) in ADMIN_IDS:
            return {
                'level': 'admin',
                'status': '👑 Администратор',
                'daily_limit': 999,
                'priority': True,
                'color': 'gold'
            }

        # Бан
        if rep <= 0:
            return {
                'level': 'banned',
                'status': '⛔ Забанен',
                'daily_limit': 0,
                'priority': False,
                'color': 'red'
            }

        # Премиум
        if self.user_repo.is_premium(user_id):
            return {
                'level': 'premium',
                'status': '💎 Премиум',
                'daily_limit': 999,
                'priority': True,
                'color': 'gold'
            }

        # Высокая репутация (даже если гость)
        if rep >= 80:
            return {
                'level': 'vip',
                'status': '⭐ Высокая репутация',
                'daily_limit': 999,
                'priority': True,
                'color': 'green'
            }

        # Средняя репутация
        if rep >= 50:
            return {
                'level': 'trusted',
                'status': '✅ Надёжный',
                'daily_limit': 15,
                'priority': False,
                'color': 'blue'
            }

        # Гость (только если репутация ниже 50)
        if chats_count < 60:
            return {
                'level': 'guest',
                'status': '👋 Гость',
                'daily_limit': 5,
                'priority': False,
                'color': 'gray'
            }

        # Стандартные уровни
        if rep < 10:
            return {
                'level': 'limited',
                'status': '⚠️ Ограничен',
                'daily_limit': 1,
                'priority': False,
                'color': 'orange'
            }
        elif rep < 25:
            return {
                'level': 'warning',
                'status': '⚠️ Предупреждение',
                'daily_limit': 5,
                'priority': False,
                'color': 'orange'
            }
        else:  # rep 25-49
            return {
                'level': 'normal',
                'status': '👤 Пользователь',
                'daily_limit': 10,
                'priority': False,
                'color': 'gray'
            }

    def can_chat_today(self, user_id: int) -> Tuple[bool, str, int, int]:
        """
        Проверяет, может ли пользователь начать чат сегодня.

        :return: (можно, сообщение, лимит, использовано_сегодня)
        """
        # Проверка бана
        if self.user_repo.is_banned(user_id):
            user = self.user_repo.get_user(user_id)
            ban_reason = user.get('ban_reason', 'Нарушение правил')
            return False, f"⛔ Ваш аккаунт заблокирован. Причина: {ban_reason}", 0, 0

        # Получаем уровень репутации
        level = self.get_reputation_level(user_id)
        daily_limit = level['daily_limit']

        # Премиум — безлимит
        if self.user_repo.is_premium(user_id):
            return True, "💎 Премиум — безлимитное общение", 999, 0

        # Проверяем дневной лимит
        # TODO: добавить таблицу user_daily_stats
        used_today = self._get_daily_chats_count(user_id)

        if daily_limit > 0 and used_today >= daily_limit:
            return False, f"❌ Достигнут лимит ({daily_limit} чатов/день). Приходите завтра!", daily_limit, used_today

        remaining = daily_limit - used_today
        return True, f"✅ Осталось чатов: {remaining}", daily_limit, used_today

    def _get_daily_chats_count(self, user_id: int) -> int:
        """
        Возвращает количество чатов пользователя за сегодня.
        TODO: реализовать после создания таблицы user_daily_stats
        """
        # Временная заглушка
        return 0

    def increment_daily_chats(self, user_id: int) -> None:
        """
        Увеличивает счётчик чатов пользователя за сегодня.
        TODO: реализовать после создания таблицы user_daily_stats
        """
        # Премиум не учитываем
        if self.user_repo.is_premium(user_id):
            return
        # TODO: увеличить счётчик
        pass
