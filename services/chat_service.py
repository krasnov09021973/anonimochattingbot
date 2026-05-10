# services/chat_service.py
"""
Сервис для управления чатами.
Здесь:
- Создание чата между пользователями
- Проверка совпадения тем
- Завершение чата
- Сохранение истории в БД
"""

import logging
import random
from datetime import datetime
from typing import Optional, Tuple, List, Set

from repositories.user_repo import UserRepo
from repositories.chat_repo import ChatRepo
from repositories.universe import Universe

logger = logging.getLogger(__name__)


class ChatService:
    """Сервис для работы с чатами"""

    def __init__(self, universe: Universe, bot, user_repo: UserRepo, chat_repo: ChatRepo):
        """
        Инициализация сервиса чатов.

        :param universe: единое хранилище состояний
        :param bot: экземпляр бота (для отправки сообщений)
        :param user_repo: репозиторий пользователей
        :param chat_repo: репозиторий чатов
        """
        self.universe = universe
        self.bot = bot
        self.user_repo = user_repo
        self.chat_repo = chat_repo

    def match_topics(self, user1_id: int, user2_id: int) -> bool:
        """
        Проверяет, есть ли у пользователей общие темы.
        Возвращает True, если есть хотя бы одна общая тема.
        """
        common = self.get_common_topics(user1_id, user2_id)
        return len(common) > 0


    def get_common_topics(self, user1_id: int, user2_id: int) -> List[dict]:
        """
        Возвращает список общих тем у двух пользователей.

        :param user1_id: ID первого пользователя
        :param user2_id: ID второго пользователя
        :return: список общих тем (каждая тема — словарь с полями id, name, emoji)
        """
        # Получаем темы обоих пользователей
        user1_topics = self.user_repo.get_user_topics(user1_id)
        user2_topics = self.user_repo.get_user_topics(user2_id)

        if not user1_topics or not user2_topics:
            return []

        # Извлекаем ID тем для быстрого сравнения
        user1_topic_ids = {t['topic_id'] for t in user1_topics}
        user2_topic_ids = {t['topic_id'] for t in user2_topics}

        # Находим пересечение
        common_ids = user1_topic_ids & user2_topic_ids

        if not common_ids:
            return []

        # Возвращаем полные данные общих тем
        return [t for t in user1_topics if t['topic_id'] in common_ids]

    def select_random_common_topic(self, common_topics: List[dict]) -> Optional[dict]:
        """
        Выбирает случайную тему из списка общих.

        :param common_topics: список общих тем
        :return: случайная тема или None, если список пуст
        """
        if not common_topics:
            return None
        return random.choice(common_topics)

    def have_common_topics(self, user1_id: int, user2_id: int) -> bool:
        """
        Проверяет, есть ли у пользователей общие темы.

        :return: True если есть хотя бы одна общая тема
        """
        return len(self.get_common_topics(user1_id, user2_id)) > 0

    async def create_chat(self, user1_id: int, user2_id: int) -> bool:
        """
        Создаёт чат между двумя пользователями.

        Что делает:
        1. Проверяет, что оба пользователя не в чате
        2. Выбирает случайную общую тему (если есть)
        3. Генерирует chat_token
        4. Сохраняет чат в Universe
        5. Отправляет приветственные сообщения
        6. Сохраняет чат в БД (active_chats и chat_history)

        :return: True если чат создан успешно
        """
        # Проверка, что оба пользователя не в чате
        if self.universe.is_in_chat(user1_id) or self.universe.is_in_chat(user2_id):
            logger.warning(f"Не удалось создать чат: {user1_id} или {user2_id} уже в чате")
            return False

        # Получаем общие темы и выбираем случайную
        common_topics = self.get_common_topics(user1_id, user2_id)
        selected_topic = self.select_random_common_topic(common_topics)

        # Генерируем токен чата и создаём чат в Universe
        chat_token = self.universe.create_chat(user1_id, user2_id)

        # Сохраняем чат в БД (в активные чаты)
        self.chat_repo.add_active_chat(user1_id, user2_id, chat_token)

        # Получаем данные профилей для отображения
        user1_data = self.user_repo.get_user_profile_data(user1_id)
        user2_data = self.user_repo.get_user_profile_data(user2_id)

        # Формируем информацию о собеседнике
        user2_info = self._format_partner_info(user2_data, user2_id)
        user1_info = self._format_partner_info(user1_data, user1_id)

        # Информация о теме
        topic_info = ""
        if selected_topic:
            topic_info = f"\n\n🎯 <b>Тема:</b> {selected_topic['emoji']} {selected_topic['name']}"

        # Отправляем приветственные сообщения
        welcome_text1 = f"🎉 <b>Собеседник найден!</b>"
        if user2_info:
            welcome_text1 += f"\n\n{user2_info}"
        welcome_text1 += topic_info

        welcome_text2 = f"🎉 <b>Собеседник найден!</b>"
        if user1_info:
            welcome_text2 += f"\n\n{user1_info}"
        welcome_text2 += topic_info

        # Импортируем клавиатуру здесь, чтобы избежать циклических импортов
        from handlers.keyboards import get_chat_end_keyboard

        await self.bot.send_message(
            user1_id,
            welcome_text1,
            reply_markup=get_chat_end_keyboard()
        )
        await self.bot.send_message(
            user2_id,
            welcome_text2,
            reply_markup=get_chat_end_keyboard()
        )

        logger.info(f"✅ Чат создан: {user1_id} <-> {user2_id} (тема: {selected_topic['name'] if selected_topic else 'нет'})")
        return True

    def _format_partner_info(self, user_data: dict, user_id: int) -> str:
        """
        Форматирует информацию о собеседнике для приветственного сообщения.
        Показываем только те поля, которые заполнены.
        """
        info = []

        chat_name = user_data.get('chat_name')
        if chat_name:
            info.append(f"👤 {chat_name}")

        age = user_data.get('age')
        if age:
            info.append(f"🎂 {age} лет")

        gender = user_data.get('gender')
        if gender and gender != 'unknown':
            gender_display = "Мужской" if gender == "male" else "Женский"
            info.append(f"⚧ {gender_display}")

        return "\n".join(info)

    async def end_chat(self, user_id: int, user_left_first: bool = True) -> bool:
        """
        Завершает чат для пользователя.

        Если чат был с живым собеседником, также завершает чат для партнёра.
        Если чат был с AI — завершает AI сессию.

        :param user_id: ID пользователя, который завершает чат
        :param user_left_first: кто первым вышел (True — этот пользователь)
        :return: True если чат успешно завершён
        """
        partner_id = self.universe.get_chat_partner(user_id)

        if partner_id is None:
            logger.warning(f"Пользователь {user_id} не в чате")
            return False

        # Получаем токен чата до завершения
        chat_token = self.universe.get_chat_token(user_id)
        started_at = self.universe.get_chat_started_at(user_id)

        # Сохраняем историю в БД (только для живых чатов)
        if partner_id != 0 and chat_token and started_at:
            duration = self._calculate_duration(started_at)
            self.chat_repo.save_chat_history(
                user1_id=user_id,
                user2_id=partner_id,
                started_at=started_at,
                ended_at=datetime.now().isoformat(),
                duration_seconds=duration,
                chat_token=chat_token,
                user_left_first=user_left_first
            )

            # Удаляем чат из активных в БД
            self.chat_repo.remove_active_chat(user_id)
            if partner_id != 0:
                self.chat_repo.remove_active_chat(partner_id)

        # Завершаем чат в Universe
        self.universe.end_chat(user_id)

        self.universe.clear_chat_mappings(user_id, partner_id)

        # Если партнёр — живой пользователь, завершаем и для него
        if partner_id != 0 and partner_id is not None:
            self.universe.end_chat(partner_id)

            # Отправляем уведомление партнёру
            from handlers.keyboards import remove_keyboard, get_rating_keyboard

            # 1. Информационное сообщение "Чат завершён" с убиранием клавиатуры
            await self.bot.send_message(
                partner_id,
                "👋 <b>Собеседник покинул чат</b>",
                reply_markup=remove_keyboard()
            )

            # 2. Сообщение с кнопками оценки
            rating_msg = await self.bot.send_message(
                partner_id,
                "🎯 <b>Оцените качество общения:</b>",
                reply_markup=get_rating_keyboard(user_id)
            )

            # Сохраняем ID сообщения с кнопками (чтобы потом удалить)
            self.universe.user_states.setdefault(partner_id, {})['rating_msg_id'] = rating_msg.message_id

        # Если партнёр — AI, просто завершаем AI сессию
        elif partner_id == 0:
            self.universe.end_ai_session(user_id)

        return True

    def _calculate_duration(self, started_at: str) -> int:
        """Вычисляет длительность чата в секундах"""
        try:
            start = datetime.fromisoformat(started_at)
            end = datetime.now()
            return int((end - start).total_seconds())
        except Exception:
            return 0
