"""
Репозиторий для работы с пользователями.
Все методы асинхронные. Оптимизированная версия 4.1.0
"""

import logging
from typing import Optional, Dict, List, Any
from .base_repo import BaseRepo

logger = logging.getLogger(__name__)

class UserRepo(BaseRepo):
    """Репозиторий пользователей"""

    async def _ensure_tables(self):
        """Создаёт таблицы для пользователей, если их нет"""
        # async with await self._get_connection() as db:
        db = await self._get_connection()
        # users (Добавлен явный DEFAULT 1 для is_active, так как новый юзер всегда активен)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                chat_name TEXT,
                age INTEGER,
                gender TEXT DEFAULT 'unknown',
                lang TEXT DEFAULT 'unknown',
                reputation INTEGER DEFAULT 25,
                is_premium INTEGER DEFAULT 0,
                premium_until TEXT,
                is_banned INTEGER DEFAULT 0,
                ban_reason TEXT,
                is_active INTEGER DEFAULT 1,                -- Изменено: 1 по умолчанию
                total_chats INTEGER DEFAULT 0,
                total_messages INTEGER DEFAULT 0,
                total_searches INTEGER DEFAULT 0,
                registered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_activity TEXT DEFAULT CURRENT_TIMESTAMP -- Изменено: DEFAULT при создании
            )
        ''')

        # user_photos
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                photo_file_id TEXT,
                position INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        ''')

        # user_topics
        await db.execute('''
            CREATE TABLE IF NOT EXISTS user_topics (
                user_id INTEGER,
                topic_id INTEGER,
                selected_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, topic_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE
            )
        ''')

        # topics
        await db.execute('''
            CREATE TABLE IF NOT EXISTS topics (
                topic_id INTEGER PRIMARY KEY,
                name TEXT UNIQUE,
                emoji TEXT,
                description TEXT
            )
        ''')

        # Индексы
        await db.execute('CREATE INDEX IF NOT EXISTS idx_users_activity ON users(last_activity)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_users_reputation ON users(reputation)')

        await db.commit()
        logger.info("✅ Таблицы пользователей созданы/проверены")

    async def get_user(self, user_id: int) -> Optional[Dict]:
        """Получает пользователя по ID"""
        return await self._fetch_one('SELECT * FROM users WHERE user_id = ?', (user_id,))

    async def get_user_context(self, user_id: int) -> Dict:
        """
        Возвращает ВСЁ состояние пользователя одним запросом.
        Используется в сервисах для быстрой проверки.
        """
        query = '''
            SELECT
                u.user_id,
                u.username,
                u.chat_name,
                u.age,
                u.gender,
                u.lang,
                u.reputation,
                u.is_premium,
                u.premium_until,
                u.is_banned,
                u.is_active,
                u.total_chats,
                u.total_messages,
                u.total_searches,
                COALESCE(ac.partner_id, 0) as partner_id,
                ac.chat_token,
                ac.started_at as chat_started_at,
                CASE WHEN ac.chat_token IS NOT NULL THEN 1 ELSE 0 END as in_chat,
                u.is_premium as is_premium_user,
                (SELECT COUNT(*) FROM user_topics WHERE user_id = u.user_id) > 0 as has_topics
            FROM users u
            LEFT JOIN active_chats ac ON (ac.user_id = u.user_id OR ac.partner_id = u.user_id)
            WHERE u.user_id = ?
        '''
        result = await self._fetch_one(query, (user_id,))
        return result or {}

    async def add_or_update_user_with_activity(self, user_id: int, username: str = '') -> bool:
        """
        УБРАНО ДУБЛИРОВАНИЕ: Выполняет UPSERT за ОДИН асинхронный запрос к SQLite.
        Автоматически поднимает статус активности пользователя.
        """
        query = '''
            INSERT INTO users (user_id, username, is_active, registered_at, last_activity)
            VALUES (?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username = EXCLUDED.username,
                is_active = 1,
                last_activity = CURRENT_TIMESTAMP
        '''
        return await self._execute(query, (user_id, username or None)) is not None

    async def update_activity(self, user_id: int) -> bool:
        """Обновляет время последней активности и делает пользователя активным (Вызывается из Middleware)"""
        query = '''
            UPDATE users
            SET last_activity = CURRENT_TIMESTAMP, is_active = 1
            WHERE user_id = ?
        '''
        return await self._execute(query, (user_id,)) is not None

    async def deactivate_inactive_users(self, days: int = 30) -> int:
        """
        Деактивирует пользователей, которые не заходили более N дней.
        Безопасное вычисление даты на уровне модификаторов SQLite.
        """
        query = '''
            UPDATE users
            SET is_active = 0
            WHERE last_activity < datetime('now', '-' || ? || ' days') AND is_active = 1
        '''
        cursor = await self._execute(query, (str(days),))
        return cursor.rowcount if cursor else 0

    async def get_active_users(self, limit: int = 1000) -> List[Dict]:
        """Возвращает список активных пользователей для рассылки"""
        query = '''
            SELECT user_id, username, chat_name
            FROM users
            WHERE is_active = 1 AND is_banned = 0
            ORDER BY last_activity DESC
            LIMIT ?
        '''
        return await self._fetch_all(query, (limit,))

    async def get_active_count(self) -> int:
        """Возвращает количество active пользователей"""
        row = await self._fetch_one('SELECT COUNT(*) as cnt FROM users WHERE is_active = 1 AND is_banned = 0')
        return row['cnt'] if row else 0

    async def get_user_selected_topics(self, user_id: int) -> List[int]:
        """Возвращает список ID тем, которые выбрал конкретный пользователь"""
        query = 'SELECT topic_id FROM user_topics WHERE user_id = ?'
        rows = await self._fetch_all(query, (user_id,))
        # Превращаем список словарей [{'topic_id': 1}, ...] в простой список чисел
        return [row['topic_id'] for row in rows] if rows else []

    async def get_partner_by_topics(self, user_id: int) -> Optional[Dict]:
        """
        Ищет случайного свободного пользователя, у которого есть
        совпадающие темы общения с текущим пользователем.

        Вход: user_id (ID того, кто нажал кнопку поиска)
        Выход: Словарь с данными партнера или None, если никто не найден
        """
        query = '''
            SELECT DISTINCT u.user_id, u.username, u.lang
            FROM users u
            -- 1. Присоединяем темы потенциальных партнеров
            JOIN user_topics ut_partner ON u.user_id = ut_partner.user_id
            WHERE u.is_banned = 0            -- Партнер не должен быть забанен
              AND u.user_id != ?             -- Не соединяем пользователя с самим собой

              -- 2. ГЛАВНОЕ УСЛОВИЕ: Тема партнера должна быть в списке тем текущего юзера
              AND ut_partner.topic_id IN (
                  SELECT topic_id FROM user_topics WHERE user_id = ?
              )
            -- 3. Сортируем в случайном порядке и берем первого попавшегося
            ORDER BY RANDOM()
            LIMIT 1
        '''
        # Выполняем асинхронный запрос, передавая user_id дважды (для двух знаков '?')
        return await self._fetch_one(query, (user_id, user_id))


    async def set_search_status(self, user_id: int, is_searching: bool) -> bool:
        """
        Включает или выключает режим поиска для пользователя в таблице users.
        """
        # Превращаем Boolean (True/False) в число для SQLite (1/0)
        status_value = 1 if is_searching else 0

        query = 'UPDATE users SET is_searching = ? WHERE user_id = ?'
        return await self._execute(query, (status_value, user_id)) is not None

    async def update_user_lang(self, user_id: int, lang: str) -> bool:
        """Обновляет пользовательский язык"""
        query = 'UPDATE users SET lang = ? WHERE user_id = ?'
        return await self._execute(query, (lang, user_id)) is not None

