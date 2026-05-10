# repositories/user_repo.py
"""
Репозиторий для работы с пользователями.
Таблицы: users, user_photos, user_topics
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List, Any

from .base_repo import BaseRepo

logger = logging.getLogger(__name__)


class UserRepo(BaseRepo):
    """Репозиторий пользователей"""

    def _ensure_tables(self):
        """Создаёт таблицы для пользователей, если их нет"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    chat_name TEXT,
                    age INTEGER,
                    gender TEXT DEFAULT 'unknown',
                    reputation INTEGER DEFAULT 25,
                    is_premium BOOLEAN DEFAULT 0,
                    premium_until TIMESTAMP,
                    is_banned BOOLEAN DEFAULT 0,
                    ban_reason TEXT,
                    total_chats INTEGER DEFAULT 0,
                    total_messages INTEGER DEFAULT 0,
                    total_searches INTEGER DEFAULT 0,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP
                )
            ''')

            # Таблица фото пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_photos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    photo_file_id TEXT,
                    position INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            ''')

            # Таблица тем пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_topics (
                    user_id INTEGER,
                    topic_id INTEGER,
                    selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, topic_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                    FOREIGN KEY (topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE
                )
            ''')

            # Индексы для быстрого поиска
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_activity ON users(last_activity)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_reputation ON users(reputation)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_premium ON users(is_premium)')

            conn.commit()
            logger.info("✅ Таблицы пользователей созданы/проверены")

    # ========== ОСНОВНЫЕ ОПЕРАЦИИ ==========

    def get_user(self, user_id: int) -> Optional[Dict]:
        """
        Получает пользователя по ID.
        Возвращает словарь с данными или None.
        """
        return self._fetch_one('SELECT * FROM users WHERE user_id = ?', (user_id,))


    def get_user_profile_data(self, user_id: int) -> Optional[Dict]:
        """Получает полные данные профиля пользователя."""
        user = self.get_user(user_id)
        if not user:
            return None

        # Добавляем темы
        user['topics'] = self.get_user_topics(user_id)
        user['topics_count'] = len(user['topics'])

        # Добавляем фото
        photos = self.get_user_photos(user_id)
        user['main_photo'] = photos[0] if photos else None
        user['photos'] = photos

        # Добавляем флаг администратора
        user['is_admin'] = self.is_admin(user_id)

        # Добавляем статус премиума
        user['is_premium'] = self.is_premium(user_id)
        user['premium_until'] = self.get_premium_expiry(user_id)

        # # Добавляем уровень репутации (для отображения в админке)
        # from services.rating_service import RatingService
        # rating_service = RatingService(universe, user_repo, chat_repo)
        # rep_level = rating_service.get_reputation_level(user_id)
        # user['reputation_level'] = rep_level['level']
        # user['reputation_status'] = rep_level['status']

        return user

    def add_or_update_user(self, user_id: int, username: str = '', first_name: str = '', last_name: str = '') -> bool:
        """
        Добавляет нового пользователя или обновляет существующего.

        Если пользователь есть — обновляем username и last_activity.
        Если нет — создаём новую запись.
        """
        # Проверяем, есть ли пользователь
        existing = self.get_user(user_id)

        if existing:
            # Обновляем
            query = '''
                UPDATE users
                SET username = ?, last_activity = CURRENT_TIMESTAMP
                WHERE user_id = ?
            '''
            return self._execute(query, (username or None, user_id)) is not None
        else:
            # Создаём нового
            query = '''
                INSERT INTO users (user_id, username, registered_at, last_activity)
                VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            '''
            return self._execute(query, (user_id, username or None)) is not None

    def update_activity(self, user_id: int) -> bool:
        """Обновляет время последней активности пользователя"""
        return self._execute('UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = ?', (user_id,)) is not None

    # ============ АДМИН ============

    def is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь администратором"""
        from config import ADMIN_IDS
        return str(user_id) in ADMIN_IDS

    # ========== РЕПУТАЦИЯ ==========

    def get_reputation(self, user_id: int) -> int:
        """Возвращает репутацию пользователя (по умолчанию 25)"""
        user = self.get_user(user_id)
        return user.get('reputation', 25) if user else 25

    def change_reputation(self, user_id: int, delta: int, reason: str = '') -> tuple:
        """
        Изменяет репутацию пользователя.

        :return: (успех, новое_значение, сообщение)
        """
        current = self.get_reputation(user_id)
        new_value = current + delta

        # Ограничиваем диапазон 0-100
        if new_value < 0:
            new_value = 0
        elif new_value > 100:
            new_value = 100

        query = 'UPDATE users SET reputation = ? WHERE user_id = ?'
        success = self._execute(query, (new_value, user_id)) is not None

        if success:
            logger.info(f"[REP] {user_id}: {current} -> {new_value} (delta={delta}, reason={reason})")

            # Проверяем, не нужно ли забанить (репутация 0)
            if new_value <= 0:
                self.ban_user(user_id, reason=f"Автобан: репутация {new_value}")
                return True, new_value, "⚠️ Репутация упала до 0 — доступ заблокирован"

            return True, new_value, f"Репутация изменена: {current} → {new_value}"

        return False, current, "Ошибка изменения репутации"

    # ========== ПРЕМИУМ ==========

    def set_premium(self, user_id: int, duration_days: int = 30) -> bool:
        """
        Выдаёт премиум на определённое количество дней.
        duration_days: 7, 30, 180, 365 или 0 (навсегда)
        """
        from datetime import datetime, timedelta

        if duration_days == 0:
            # Навсегда
            query = 'UPDATE users SET is_premium = 1, premium_until = NULL WHERE user_id = ?'
            return self._execute(query, (user_id,)) is not None
        else:
            until = (datetime.now() + timedelta(days=duration_days)).isoformat()
            query = 'UPDATE users SET is_premium = 1, premium_until = ? WHERE user_id = ?'
            return self._execute(query, (until, user_id)) is not None

    def revoke_premium(self, user_id: int) -> bool:
        """Снимает премиум с пользователя"""
        query = 'UPDATE users SET is_premium = 0, premium_until = NULL WHERE user_id = ?'
        return self._execute(query, (user_id,)) is not None

    def is_premium(self, user_id: int) -> bool:
        """Проверяет, активен ли премиум у пользователя"""
        user = self.get_user(user_id)
        if not user or not user.get('is_premium'):
            return False

        premium_until = user.get('premium_until')
        if premium_until is None:
            return True  # навсегда

        # Проверяем, не истёк ли срок
        from datetime import datetime
        return datetime.now() < datetime.fromisoformat(premium_until)

    def get_premium_expiry(self, user_id: int) -> Optional[str]:
        """
        Возвращает дату окончания премиума в формате ISO.
        Если премиум навсегда — возвращает 'forever'.
        Если премиума нет — возвращает None.
        """
        user = self.get_user(user_id)
        if not user or not user.get('is_premium'):
            return None

        premium_until = user.get('premium_until')
        if premium_until is None:
            return 'forever'

        return premium_until

    # ========== БАН ==========

    def ban_user(self, user_id: int, reason: str = '') -> bool:
        """Блокирует пользователя"""
        query = 'UPDATE users SET is_banned = 1, ban_reason = ? WHERE user_id = ?'
        return self._execute(query, (reason, user_id)) is not None

    def unban_user(self, user_id: int) -> bool:
        """Разблокирует пользователя"""
        query = 'UPDATE users SET is_banned = 0, ban_reason = NULL WHERE user_id = ?'
        return self._execute(query, (user_id,)) is not None

    def is_banned(self, user_id: int) -> bool:
        """Проверяет, забанен ли пользователь"""
        user = self.get_user(user_id)
        return user.get('is_banned', False) if user else False

    # ========== ПРОФИЛЬ (имя, возраст, пол) ==========

    def update_chat_name(self, user_id: int, chat_name: str) -> bool:
        """Обновляет отображаемое имя в чате"""
        return self._execute('UPDATE users SET chat_name = ? WHERE user_id = ?', (chat_name, user_id)) is not None

    def update_age(self, user_id: int, age: int) -> bool:
        """Обновляет возраст"""
        return self._execute('UPDATE users SET age = ? WHERE user_id = ?', (age, user_id)) is not None

    def update_gender(self, user_id: int, gender: str) -> bool:
        """Обновляет пол (male/female/unknown)"""
        return self._execute('UPDATE users SET gender = ? WHERE user_id = ?', (gender, user_id)) is not None

    # ========== СТАТИСТИКА ==========

    def increment_chats_count(self, user_id: int) -> bool:
        """Увеличивает счётчик чатов пользователя"""
        return self._execute('UPDATE users SET total_chats = total_chats + 1 WHERE user_id = ?', (user_id,)) is not None

    def increment_messages_count(self, user_id: int) -> bool:
        """Увеличивает счётчик сообщений"""
        return self._execute('UPDATE users SET total_messages = total_messages + 1 WHERE user_id = ?', (user_id,)) is not None

    def increment_searches_count(self, user_id: int) -> bool:
        """Увеличивает счётчик поисков"""
        return self._execute('UPDATE users SET total_searches = total_searches + 1 WHERE user_id = ?', (user_id,)) is not None

    # ========== ФОТО ==========

    def get_user_photos(self, user_id: int) -> List[str]:
        """
        Возвращает список photo_file_id всех фото пользователя.
        Первое фото — основное (position = 0), остальные — дополнительные.
        """
        rows = self._fetch_all('SELECT photo_file_id FROM user_photos WHERE user_id = ? ORDER BY position', (user_id,))
        return [row['photo_file_id'] for row in rows]

    def add_photo(self, user_id: int, photo_file_id: str) -> bool:
        """Добавляет фото пользователю (в конец)"""
        # Получаем текущий максимальный position
        rows = self._fetch_all('SELECT MAX(position) as max_pos FROM user_photos WHERE user_id = ?', (user_id,))
        max_pos = rows[0]['max_pos'] if rows and rows[0]['max_pos'] is not None else -1
        new_pos = max_pos + 1

        return self._execute(
            'INSERT INTO user_photos (user_id, photo_file_id, position) VALUES (?, ?, ?)',
            (user_id, photo_file_id, new_pos)
        ) is not None

    def delete_photo(self, user_id: int, position: int) -> bool:
        """Удаляет фото по позиции и переупорядочивает остальные"""
        # Удаляем фото
        success = self._execute('DELETE FROM user_photos WHERE user_id = ? AND position = ?', (user_id, position))

        if success:
            # Сдвигаем позиции оставшихся фото
            self._execute('UPDATE user_photos SET position = position - 1 WHERE user_id = ? AND position > ?', (user_id, position))

        return success is not None

    def delete_all_photos(self, user_id: int) -> bool:
        """Удаляет все фото пользователя"""
        return self._execute('DELETE FROM user_photos WHERE user_id = ?', (user_id,)) is not None

    # ========== ТЕМЫ/ИНТЕРЕСЫ ==========

    def get_user_topics(self, user_id: int) -> List[Dict]:
        """Возвращает список тем пользователя"""
        query = '''
            SELECT t.topic_id, t.name, t.emoji
            FROM user_topics ut
            JOIN topics t ON ut.topic_id = t.topic_id
            WHERE ut.user_id = ?
            ORDER BY t.name
        '''
        return self._fetch_all(query, (user_id,))

    def add_user_topic(self, user_id: int, topic_id: int) -> bool:
        """Добавляет тему пользователю"""
        return self._execute('INSERT INTO user_topics (user_id, topic_id) VALUES (?, ?)', (user_id, topic_id)) is not None

    def remove_user_topic(self, user_id: int, topic_id: int) -> bool:
        """Удаляет тему у пользователя"""
        return self._execute('DELETE FROM user_topics WHERE user_id = ? AND topic_id = ?', (user_id, topic_id)) is not None

    def clear_user_topics(self, user_id: int) -> bool:
        """Удаляет все темы пользователя"""
        return self._execute('DELETE FROM user_topics WHERE user_id = ?', (user_id,)) is not None

    # ========== ПАГИНАЦИЯ И УДАЛЕНИЕ ==========

    def get_users_paginated(self, page: int = 1, limit: int = 20, search: str = "") -> dict:
        """
        Возвращает список пользователей с пагинацией и поиском.
        """
        offset = (page - 1) * limit
        search_filter = f"%{search}%"

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()

                # Подсчёт общего количества
                if search:
                    cursor.execute('''
                        SELECT COUNT(*) FROM users
                        WHERE user_id LIKE ? OR username LIKE ? OR chat_name LIKE ?
                    ''', (search_filter, search_filter, search_filter))
                else:
                    cursor.execute('SELECT COUNT(*) FROM users')
                total = cursor.fetchone()[0]

                # Получение списка
                if search:
                    cursor.execute('''
                        SELECT user_id, username, chat_name, reputation, total_chats, total_messages,
                            is_premium, premium_until, is_banned
                        FROM users
                        WHERE user_id LIKE ? OR username LIKE ? OR chat_name LIKE ?
                        ORDER BY user_id DESC
                        LIMIT ? OFFSET ?
                    ''', (search_filter, search_filter, search_filter, limit, offset))
                else:
                    cursor.execute('''
                        SELECT user_id, username, chat_name, reputation, total_chats, total_messages,
                            is_premium, premium_until, is_banned
                        FROM users
                        ORDER BY user_id DESC
                        LIMIT ? OFFSET ?
                    ''', (limit, offset))

                users = [dict(row) for row in cursor.fetchall()]

                return {
                    "users": users,
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "total_pages": (total + limit - 1) // limit if total > 0 else 1
                }
        except Exception as e:
            logger.error(f"Ошибка get_users_paginated: {e}")
            return {"users": [], "total": 0, "page": page, "limit": limit, "total_pages": 1}

    def delete_user(self, user_id: int) -> bool:
        """
        Полностью удаляет пользователя и все связанные данные.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Удаляем связанные данные
                cursor.execute('DELETE FROM user_photos WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM user_topics WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM reports WHERE reporter_id = ? OR reported_id = ?', (user_id, user_id))
                cursor.execute('DELETE FROM chat_history WHERE user1_id = ? OR user2_id = ?', (user_id, user_id))
                cursor.execute('DELETE FROM ratings WHERE rater_id = ? OR rated_id = ?', (user_id, user_id))
                cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
                conn.commit()
                logger.info(f"Пользователь {user_id} полностью удалён")
                return True
        except Exception as e:
            logger.error(f"Ошибка удаления пользователя {user_id}: {e}")
            return False
