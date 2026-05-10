# repositories/chat_repo.py
"""
Репозиторий для работы с чатами.
Таблицы: active_chats, chat_history, ratings
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List

from .base_repo import BaseRepo

logger = logging.getLogger(__name__)


class ChatRepo(BaseRepo):
    """Репозиторий чатов"""

    def _ensure_tables(self):
        """Создаёт таблицы для чатов, если их нет"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Активные чаты (кто с кем сейчас)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS active_chats (
                    user1_id INTEGER,
                    user2_id INTEGER,
                    chat_token TEXT,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user1_id, user2_id)
                )
            ''')

            # История чатов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user1_id INTEGER,
                    user2_id INTEGER,
                    chat_token TEXT,
                    started_at TIMESTAMP,
                    ended_at TIMESTAMP,
                    duration_seconds INTEGER,
                    user1_left_first BOOLEAN
                )
            ''')

            # Оценки пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ratings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rater_id INTEGER,
                    rated_id INTEGER,
                    rating TEXT CHECK(rating IN ('good', 'bad')),
                    chat_token TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(rater_id, rated_id, chat_token)
                )
            ''')

            # Индексы
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_history_users ON chat_history(user1_id, user2_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ratings_rater ON ratings(rater_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ratings_rated ON ratings(rated_id)')

            conn.commit()
            logger.info("✅ Таблицы чатов созданы/проверены")

    # ========== АКТИВНЫЕ ЧАТЫ ==========

    def add_active_chat(self, user1_id: int, user2_id: int, chat_token: str) -> bool:
        """Добавляет запись об активном чате в БД"""
        query = '''
            INSERT OR REPLACE INTO active_chats (user1_id, user2_id, chat_token, started_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        '''
        return self._execute(query, (user1_id, user2_id, chat_token)) is not None

    def remove_active_chat(self, user_id: int, chat_token: str) -> bool:
        """Удаляет все записи активных чатов для пользователя"""
        query = 'DELETE FROM active_chats WHERE (user1_id = ? OR user2_id = ?) AND chat_token = ?'
        return self._execute(query, (user_id, user_id, chat_token)) is not None

    def get_active_chats(self) -> List[Dict]:
        """Возвращает список всех активных чатов"""
        return self._fetch_all('SELECT * FROM active_chats')

    # ========== ИСТОРИЯ ЧАТОВ ==========

    def save_chat_history(self, user1_id: int, user2_id: int, started_at: str, ended_at: str,
                          duration_seconds: int, chat_token: str, user_left_first: bool) -> bool:
        """Сохраняет завершённый чат в историю"""
        query = '''
            INSERT INTO chat_history (user1_id, user2_id, chat_token, started_at, ended_at, duration_seconds, user1_left_first)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        return self._execute(query, (user1_id, user2_id, chat_token, started_at, ended_at, duration_seconds, user_left_first)) is not None

    def get_chat_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Возвращает историю чатов пользователя"""
        query = '''
            SELECT * FROM chat_history
            WHERE user1_id = ? OR user2_id = ?
            ORDER BY ended_at DESC
            LIMIT ?
        '''
        return self._fetch_all(query, (user_id, user_id, limit))

    # ========== ОЦЕНКИ ==========

    def has_rated(self, rater_id: int, rated_id: int, chat_token: str) -> bool:
        """Проверяет, оценивал ли пользователь уже в этом чате"""
        query = 'SELECT 1 FROM ratings WHERE rater_id = ? AND rated_id = ? AND chat_token = ?'
        row = self._fetch_one(query, (rater_id, rated_id, chat_token))
        return row is not None

    def add_rating(self, rater_id: int, rated_id: int, rating: str, chat_token: str) -> bool:
        """Добавляет оценку пользователя"""
        query = 'INSERT INTO ratings (rater_id, rated_id, rating, chat_token) VALUES (?, ?, ?, ?)'
        result = self._execute(query, (rater_id, rated_id, rating, chat_token))
        return result is not None

    def get_ratings_received(self, user_id: int) -> List[Dict]:
        """Возвращает все оценки, полученные пользователем"""
        query = 'SELECT * FROM ratings WHERE rated_id = ? ORDER BY created_at DESC'
        return self._fetch_all(query, (user_id,))
