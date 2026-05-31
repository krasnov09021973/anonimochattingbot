# services/user_service.py
"""
Сервис для обработки пользователей.
"""

import logging
from typing import Dict, Optional

from repositories.user_repo import UserRepo
from repositories.topic_repo import TopicRepo
# from services.ai_service import AIService
# from services.limits_service import LimitsService
from lang import get_error

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self, user_repo: UserRepo, topic_repo: TopicRepo):
        self.user_repo = user_repo
        self.topic_repo = topic_repo
        self._lang_cache = {}  # {user_id: lang_code}

    # Кусочек логики внутри UserService
    async def register_or_resume_user(self, user_id: int, username: str) -> None:
        # Репозиторий делает один INSERT OR REPLACE, который сразу пишет и юзера, и timestamp активности
        await self.user_repo.add_or_update_user_with_activity(user_id, username)


    async def track_activity(self, user_id: int) -> None:
        """Быстрое обновление активности пользователя (вызывается из Middleware)"""
        try:
            # Вызываем метод репозитория, который мы обновили ранее
            await self.user_repo.update_activity(user_id)
        except Exception as e:
            # Логируем ошибку, но не ломаем работу бота для пользователя
            logger.error(f"Не удалось обновить активность для пользователя {user_id}: {e}")

    async def get_user_language(self, user_id: int) -> str:
        """Быстро возвращает язык из ОЗУ. Если там нет — лезет в БД один раз"""
        # 1. Проверяем, есть ли язык в быстрой памяти
        if user_id in self._lang_cache:
            return self._lang_cache[user_id]

        # 2. Если нет (например, бот перезапустился), берем из БД
        try:
            user_ctx = await self.user_repo.get_user_context(user_id)
            lang = user_ctx.get('lang', 'ru') if user_ctx else 'ru'
            if lang == 'unknown':
                lang = 'ru'
        except Exception:
            lang = 'ru'

        # 3. Сохраняем в кэш, чтобы больше не дергать БД
        self._lang_cache[user_id] = lang
        return lang

    async def set_user_language(self, user_id: int, lang: str):
        """Метод для смены языка (вызывать, если юзер меняет настройки)"""
        await self.user_repo.update_user_lang(user_id, lang) # Обновляем в БД
        self._lang_cache[user_id] = lang                     # Сразу обновляем в кэше
