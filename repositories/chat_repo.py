# repositories/chat_repo.py
"""
Репозиторий для работы с чатами.
Таблицы: active_chats, chat_history, ratings, message_mapping
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List

from .base_repo import BaseRepo

logger = logging.getLogger(__name__)


class ChatRepo(BaseRepo):
    """Репозиторий чатов"""

    async def _ensure_tables(self):
        """Создаёт все таблицы для чатов"""
        # async with await self._get_connection() as db:
        db = await self._get_connection()
        # Активные чаты
        await db.execute('''
            CREATE TABLE IF NOT EXISTS active_chats (
                chat_token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                partner_id INTEGER NOT NULL,
                started_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                user_rated BOOLEAN DEFAULT 0,
                partner_rated BOOLEAN DEFAULT 0,
                PRIMARY KEY (user_id, partner_id)
            )
        ''')

        # История чатов
        await db.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_token TEXT UNIQUE,
                user_id INTEGER,
                partner_id INTEGER,
                started_at TEXT,
                ended_at TEXT,
                duration_seconds INTEGER,
                user_left_first BOOLEAN,
                PRIMARY KEY ("id"),
                FOREIGN KEY (partner_id) REFERENCES users(user_id) ON UPDATE NO ACTION ON DELETE NO ACTION,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON UPDATE NO ACTION ON DELETE NO ACTION
            )
        ''')

        # Оценки
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ratings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                partner_id INTEGER,
                rating TEXT CHECK(rating IN ('good', 'bad')),
                chat_token TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Маппинг сообщений (для реакций)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS message_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_token TEXT,
                user_id INTEGER,
                original_msg_id INTEGER,
                cloned_msg_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_token) REFERENCES active_chats(chat_token)
            )
        ''')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_chat_history_users ON chat_history(user_id, partner_id)')

        await db.commit()
        logger.info("✅ Таблицы чатов созданы/проверены")

    # ========== АКТИВНЫЕ ЧАТЫ ==========

    async def create_active_chat(self, user1_id: int, user2_id: int) -> str:
        """
        ОПТИМИЗИРОВАНО: Создаёт запись активного чата.
        Генерирует chat_token и пишет текущее время на уровне базы SQLite.

        Вход: user1_id (Ваш ID), user2_id (ID партнера)
        Выход: Строка с токеном созданного чата (str)
        """
        import uuid
        # Генерируем уникальный токен диалога
        chat_token = str(uuid.uuid4())

        # ИСПРАВЛЕНО: Используем ваши новые имена полей: user_id и partner_id
        # Использование CURRENT_TIMESTAMP в SQLite надежнее, чем isoformat() из Python
        query = '''
            INSERT INTO active_chats (chat_token, user_id, partner_id, started_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        '''
        await self._execute(query, (chat_token, user1_id, user2_id))
        return chat_token

    async def get_active_chat(self, chat_token: str) -> Optional[Dict]:
        """Получает активный чат по токену"""
        return await self._fetch_one('SELECT * FROM active_chats WHERE chat_token = ?', (chat_token,))

    async def get_active_chat_by_user(self, user_id: int) -> Optional[Dict]:
        """
        Находит активный чат по ID любого из участников.
        ИСПРАВЛЕНО: поля приведены к user_id и partner_id.
        """
        query = '''
            SELECT * FROM active_chats
            WHERE user_id = ? OR partner_id = ?
        '''
        return await self._fetch_one(query, (user_id, user_id))

    async def delete_active_chat(self, chat_token: str) -> bool:
        """Удаляет запись активного чата (при полном закрытии)"""
        query = 'DELETE FROM active_chats WHERE chat_token = ?'
        return await self._execute(query, (chat_token,)) is not None

    # ========== ИСТОРИЯ ЧАТОВ ==========

    async def save_to_history(
        self,
        chat_token: str,
        user1_id: int,
        user2_id: int,
        started_at: str,
        ended_at: str,
        duration_seconds: int,
        user1_left_first: bool = True
    ) -> bool:
        """
        Сохраняет завершённый чат в историю.
        ИСПРАВЛЕНО: Поля приведены к стандарту user_id и partner_id.
        """
        query = '''
            INSERT INTO chat_history (chat_token, user_id, partner_id, started_at, ended_at, duration_seconds, user_left_first)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        # Конвертируем Boolean в число для SQLite (1 или 0)
        left_first_value = 1 if user1_left_first else 0

        return await self._execute(query, (
            chat_token, user1_id, user2_id, started_at, ended_at, duration_seconds, left_first_value
        )) is not None

    async def get_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        Возвращает историю чатов пользователя.
        ИСПРАВЛЕНО: Поля приведены к стандарту user_id и partner_id.
        """
        query = '''
            SELECT * FROM chat_history
            WHERE user_id = ? OR partner_id = ?
            ORDER BY ended_at DESC
            LIMIT ?
        '''
        return await self._fetch_all(query, (user_id, user_id, limit))

    # async def create_active_chat(self, user1_id: int, user2_id: int, chat_token: str) -> bool:
    #     """Создаёт запись активного чата"""
    #     query = '''
    #         INSERT INTO active_chats (chat_token, user_id, partner_id, started_at, is_active)
    #         VALUES (?, ?, ?, ?, 1)
    #     '''
    #     return await self._execute(query, (chat_token, user1_id, user2_id, datetime.now().isoformat())) is not None
    #
    # async def get_active_chat(self, chat_token: str) -> Optional[Dict]:
    #     """Получает активный чат по токену"""
    #     return await self._fetch_one('SELECT * FROM active_chats WHERE chat_token = ?', (chat_token,))
    #
    # async def get_active_chat_by_user(self, user_id: int) -> Optional[Dict]:
    #     """Находит активный чат по ID пользователя"""
    #     query = '''
    #         SELECT * FROM active_chats
    #         WHERE (user_id = ? OR partner_id = ?) AND is_active = 1
    #     '''
    #     return await self._fetch_one(query, (user_id, user_id))
    #
    # async def deactivate_chat(self, chat_token: str) -> bool:
    #     """Деактивирует чат (устанавливает is_active = 0)"""
    #     query = 'UPDATE active_chats SET is_active = 0 WHERE chat_token = ?'
    #     return await self._execute(query, (chat_token,)) is not None

    async def delete_active_chat(self, chat_token: str) -> bool:
        """Удаляет запись активного чата"""
        query = 'DELETE FROM active_chats WHERE chat_token = ?'
        return await self._execute(query, (chat_token,)) is not None

    async def clear_active_chats(self) -> bool:
        """Удаляет запись активного чата"""
        return await self._execute('DELETE FROM active_chats') is not None

    # ========== ОЦЕНКИ ==========

    async def add_rating(self, user_id: int, partner_id: int, rating: str, chat_token: str) -> bool:
        """Добавляет оценку пользователя"""
        query = 'INSERT INTO ratings (user_id, partner_id, rating, chat_token) VALUES (?, ?, ?, ?)'
        return await self._execute(query, (user_id, partner_id, rating, chat_token)) is not None

    async def has_rated(self, user_id: int, chat_token: str) -> bool:
        """Проверяет, оценивал ли пользователь этот чат"""
        query = 'SELECT 1 FROM ratings WHERE user_id = ? AND chat_token = ?'
        result = await self._fetch_one(query, (user_id, chat_token))
        return result is not None

    async def mark_rated(self, user_id: int, chat_token: str) -> bool:
        """Отмечает, что пользователь оценил чат (в active_chats)"""
        # Сначала определяем, является ли пользователь user1 или user2
        chat = await self.get_active_chat(chat_token)
        if not chat:
            return False

        if chat['user1_id'] == user_id:
            field = 'user_rated'
        else:
            field = 'partner_rated'

        query = f'UPDATE active_chats SET {field} = 1 WHERE chat_token = ?'
        return await self._execute(query, (chat_token,)) is not None

    # ========== ИСТОРИЯ ЧАТОВ ==========

    async def save_to_history(
        self,
        chat_token: str,
        user1_id: int,
        user2_id: int,
        started_at: str,
        ended_at: str,
        duration_seconds: int,
        user1_left_first: bool = True
    ) -> bool:
        """Сохраняет завершённый чат в историю"""
        query = '''
            INSERT INTO chat_history (chat_token, user_id, partner_id, started_at, ended_at, duration_seconds, user_left_first)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        return await self._execute(query, (chat_token, user1_id, user2_id, started_at, ended_at, duration_seconds, user1_left_first)) is not None

    async def get_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Возвращает историю чатов пользователя"""
        query = '''
            SELECT * FROM chat_history
            WHERE user1_id = ? OR user2_id = ?
            ORDER BY ended_at DESC
            LIMIT ?
        '''
        return await self._fetch_all(query, (user_id, user_id, limit))

    # ========== МАППИНГ СООБЩЕНИЙ (ДЛЯ РЕАКЦИЙ) ==========

    async def add_message_mapping(self, chat_token: str, user_id: int, original_msg_id: int, cloned_msg_id: int) -> bool:
        """Сохраняет маппинг сообщений для реакций"""
        query = '''
            INSERT INTO message_mapping (chat_token, user_id, original_msg_id, cloned_msg_id)
            VALUES (?, ?, ?, ?)
        '''
        return await self._execute(query, (chat_token, user_id, original_msg_id, cloned_msg_id)) is not None

    async def get_cloned_msg_id(self, chat_token: str, user_id: int, original_msg_id: int) -> Optional[int]:
        """Возвращает ID клонированного сообщения"""
        query = 'SELECT cloned_msg_id FROM message_mapping WHERE chat_token = ? AND user_id = ? AND original_msg_id = ?'
        result = await self._fetch_one(query, (chat_token, user_id, original_msg_id))
        return result['cloned_msg_id'] if result else None

    async def clear_mappings(self, chat_token: str) -> bool:
        """Удаляет все маппинги для чата"""
        query = 'DELETE FROM message_mapping WHERE chat_token = ?'
        return await self._execute(query, (chat_token,)) is not None
