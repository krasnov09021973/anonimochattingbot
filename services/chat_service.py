# services/chat_service.py
"""
Сервис для обработки чатов.
Единая точка входа для всех сообщений.
"""

import logging
from typing import Dict, Optional

from repositories.user_repo import UserRepo
from repositories.chat_repo import ChatRepo
from services.limits_service import LimitsService
from services.ai_service import AIService
from lang import get_error
from lang import get_error

logger = logging.getLogger(__name__)

class ChatService:
    """Сервис для управления чатами"""

    def __init__(self, user_repo: UserRepo, chat_repo: ChatRepo, limits_service: LimitsService, ai_service: Optional[AIService] = None):
        self.user_repo = user_repo
        self.chat_repo = chat_repo
        self.limits_service = limits_service
        self.ai_service = ai_service

    async def process_incoming_message(self, user_id: int, text: str) -> Dict:
        """
        Единая точка входа для всех текстовых сообщений.

        Возвращает:
            {'status': 'sent_to_partner'} — сообщение отправлено партнёру
            {'status': 'ai_reply', 'text': str} — ответ AI
            {'status': 'searching'} — пользователь в поиске
            {'status': 'no_active_session'} — нет активной сессии
        """
        # 1. Проверка лимитов
        # if not await self.limits_service.can_send_message(user_id):
        #     return {'status': 'limit_exceeded', 'error': get_error('limit_exceeded')}

        # 2. Получаем состояние пользователя (один запрос)
        user = await self.user_repo.get_user_context(user_id)

        if not user:
            return {'status': 'no_active_session', 'error': get_error('no_active_session')}

        # 3. Маршрутизация сообщения
        partner_id = user.get('partner_id', 0)

        if partner_id > 0:
            # Чат с живым собеседником
            # await self._send_to_partner(user_id, partner_id, text)
            # return {'status': 'sent_to_partner'}
            return

        # elif partner_id == 0 and user.get('in_chat'):
        #     # Чат с AI
        #     if self.ai_service:
        #         reply = await self.ai_service.generate_reply(user_id, text)
        #         return {'status': 'ai_reply', 'text': reply}
        #     else:
        #         return {'status': 'error', 'error': get_error('ai_error')}

        else:
            # Нет активного чата
            return {'status': 'no_active_session', 'error': get_error('no_active_session')}

    async def clear_all_active_chats(self) -> None:
        """
        УНИЧТОЖЕНИЕ МУСОРА: Полностью вычищает таблицу активных чатов в БД.
        Вызывается строго при выключении бота (в lifespan), чтобы
        'призраки старой базы' не блокировали пользователей при перезапуске.
        """
        try:
            # Вызываем метод удаления прямо из репозитория чатов
            # В вашем ChatRepo уже есть метод удаления, мы можем написать там очистку всей таблицы
            await self.chat_repo.clear_active_chats()
            logger.info("🧹 Все активные сессии чатов успешно стерты из базы данных.")
        except Exception as e:
            logger.error(f"Не удалось очистить активные чаты: {e}")

    # async def _send_to_partner(self, from_user_id: int, to_user_id: int, text: str) -> bool:
    #     """
    #     Отправляет сообщение партнёру.
    #     Здесь будет логика отправки через Telegram бота.
    #     """
    #     try:
    #         # Получаем экземпляр бота из глобальных зависимостей
    #         from utils.deps import get_bot
    #         bot = get_bot()
    #
    #         await bot.send_message(to_user_id, text)
    #         logger.info(f"Сообщение переслано от {from_user_id} к {to_user_id}")
    #         return True
    #     except Exception as e:
    #         logger.error(f"Ошибка отправки сообщения: {e}")
    #         return False
    #
    # async def close_chat(self, user_id: int) -> int:
    #     """
    #     Закрывает чат для пользователя.
    #     Возвращает ID партнёра (0 для AI, None если чата не было).
    #     """
    #     user = await self.user_repo.get_user_context(user_id)
    #     partner_id = user.get('partner_id', 0)
    #
    #     if not user.get('in_chat'):
    #         return None
    #
    #     # Очищаем связи в репозитории
    #     if partner_id > 0:
    #         await self.chat_repo.clear_chat_connection(user_id, partner_id)
    #     else:
    #         await self.chat_repo.clear_ai_chat(user_id)
    #
    #     return partner_id
    #
    # async def get_partner_info(self, user_id: int) -> Optional[Dict]:
    #     """
    #     Возвращает информацию о собеседнике для кнопки "👤 Профиль"
    #     """
    #     user = await self.user_repo.get_user_context(user_id)
    #     partner_id = user.get('partner_id', 0)
    #
    #     if not partner_id:
    #         return None
    #
    #     if partner_id == 0:
    #         # AI собеседник
    #         return {
    #             'is_ai': True,
    #             'chat_name': None,  # Имя будет выбрано случайно
    #             'age': None,
    #             'gender': None,
    #             'topics': []
    #         }
    #     else:
    #         # Живой собеседник
    #         partner = await self.user_repo.get_user(partner_id)
    #         if not partner:
    #             return None
    #
    #         return {
    #             'is_ai': False,
    #             'user_id': partner['user_id'],
    #             'chat_name': partner.get('chat_name'),
    #             'age': partner.get('age'),
    #             'gender': partner.get('gender'),
    #             'reputation': partner.get('reputation', 25),
    #             'topics': await self.user_repo.get_user_topics(partner_id)
    #         }
