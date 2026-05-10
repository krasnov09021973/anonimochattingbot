# repositories/ai_repo.py
"""
Репозиторий для работы с AI.
Таблицы: ai_characters, ai_models, ai_feedback, ai_sessions
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List

from .base_repo import BaseRepo

logger = logging.getLogger(__name__)


class AIRepo(BaseRepo):
    """Репозиторий для AI"""

    def _ensure_tables(self):
        """Создаёт таблицы для AI, если их нет"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # AI персонажи
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_characters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gender TEXT CHECK(gender IN ('male', 'female')),
                    topic TEXT,
                    traits TEXT,
                    style TEXT,
                    rules TEXT,
                    prompt TEXT,
                    names TEXT,
                    min_age INTEGER DEFAULT 18,
                    max_age INTEGER DEFAULT 30,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # AI модели (OpenRouter, локальные и т.д.)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    provider TEXT,
                    is_active BOOLEAN DEFAULT 0,
                    is_free BOOLEAN DEFAULT 1,
                    max_tokens INTEGER DEFAULT 400,
                    temperature REAL DEFAULT 0.9,
                    top_p REAL DEFAULT 0.9,
                    frequency_penalty REAL DEFAULT 0.3,
                    presence_penalty REAL DEFAULT 0.2,
                    priority INTEGER DEFAULT 0
                )
            ''')

            # AI фидбек (оценки и жалобы)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    ai_name TEXT,
                    ai_age INTEGER,
                    ai_gender TEXT,
                    topic TEXT,
                    rating TEXT,
                    is_complaint BOOLEAN DEFAULT 0,
                    complaint_reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')

            # Индексы
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_feedback_user ON ai_feedback(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_feedback_ai ON ai_feedback(ai_name)')

            # AI сессии (для аналитики)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_sessions_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    character_id INTEGER,
                    messages_count INTEGER,
                    started_at TIMESTAMP,
                    ended_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (character_id) REFERENCES ai_characters(id)
                )
            ''')

            # Таблица глобальных настроек AI
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Вставляем настройки по умолчанию, если их нет
            cursor.execute('''
                INSERT OR IGNORE INTO ai_settings (key, value, description) VALUES
                    ('ai_enabled', '1', 'Включить AI-собеседника'),
                    ('ai_timeout', '15', 'Таймаут до подключения AI (секунды)'),
                    ('default_model', 'nvidia/nemotron-3-nano-30b-a3b:free', 'Модель по умолчанию'),
                    ('max_free_messages', '50', 'Лимит сообщений для бесплатных пользователей'),
                    ('temperature', '0.9', 'Температура генерации'),
                    ('max_tokens', '400', 'Максимальное количество токенов в ответе'),
                    ('top_p', '0.9', 'Top P параметр'),
                    ('frequency_penalty', '0.3', 'Frequency penalty'),
                    ('presence_penalty', '0.2', 'Presence penalty')
            ''')


            conn.commit()
            logger.info("✅ Таблицы AI созданы/проверены")

    # ========== AI ПЕРСОНАЖИ ==========

    def get_active_characters(self) -> List[Dict]:
        """Возвращает список активных AI персонажей"""
        return self._fetch_all('SELECT * FROM ai_characters WHERE is_active = 1 ORDER BY topic, gender')

    def get_character_by_topic(self, topic: str, gender: str = None) -> List[Dict]:
        """
        Возвращает персонажей по теме.
        Если gender указан — фильтруем по полу.
        """
        if gender:
            query = 'SELECT * FROM ai_characters WHERE topic = ? AND gender = ? AND is_active = 1'
            return self._fetch_all(query, (topic, gender))
        else:
            query = 'SELECT * FROM ai_characters WHERE topic = ? AND is_active = 1'
            return self._fetch_all(query, (topic,))

    def get_character_by_id(self, character_id: int) -> Optional[Dict]:
        """Возвращает персонажа по ID"""
        return self._fetch_one('SELECT * FROM ai_characters WHERE id = ?', (character_id,))

    def add_character(self, name: str, age: int, gender: str, topic: str, prompt: str) -> int:
        """Добавляет нового AI персонажа. Возвращает ID."""
        query = '''
            INSERT INTO ai_characters (name, age, gender, topic, prompt, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        '''
        cursor = self._execute(query, (name, age, gender, topic, prompt))
        return cursor.lastrowid if cursor else 0

    def update_character(self, character_id: int, **kwargs) -> bool:
        """Обновляет данные персонажа"""
        fields = []
        values = []
        for key, value in kwargs.items():
            if key in ['name', 'age', 'gender', 'topic', 'prompt', 'is_active']:
                fields.append(f"{key} = ?")
                values.append(value)

        if not fields:
            return False

        values.append(character_id)
        query = f'UPDATE ai_characters SET {", ".join(fields)} WHERE id = ?'
        return self._execute(query, tuple(values)) is not None

    def delete_character(self, character_id: int) -> bool:
        """Удаляет персонажа (или деактивирует)"""
        return self._execute('UPDATE ai_characters SET is_active = 0 WHERE id = ?', (character_id,)) is not None

    # ========== AI МОДЕЛИ ==========

    def get_active_model(self) -> Optional[Dict]:
        """Возвращает активную AI модель"""
        return self._fetch_one('SELECT * FROM ai_models WHERE is_active = 1 ORDER BY priority ASC LIMIT 1')

    def get_model_by_name(self, name: str) -> Optional[Dict]:
        """Возвращает модель по имени"""
        return self._fetch_one('SELECT * FROM ai_models WHERE name = ?', (name,))

    def set_active_model(self, model_id: int) -> bool:
        """Устанавливает активную модель (снимает активность с остальных)"""
        # Снимаем активность со всех
        self._execute('UPDATE ai_models SET is_active = 0')
        # Устанавливаем новую
        return self._execute('UPDATE ai_models SET is_active = 1 WHERE id = ?', (model_id,)) is not None

    def add_model(self, name: str, provider: str, **kwargs) -> int:
        """Добавляет новую AI модель"""
        query = '''
            INSERT INTO ai_models (name, provider, max_tokens, temperature, top_p, frequency_penalty, presence_penalty)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        cursor = self._execute(query, (
            name, provider,
            kwargs.get('max_tokens', 400),
            kwargs.get('temperature', 0.9),
            kwargs.get('top_p', 0.9),
            kwargs.get('frequency_penalty', 0.3),
            kwargs.get('presence_penalty', 0.2)
        ))
        return cursor.lastrowid if cursor else 0

    # ========== AI ФИДБЕК ==========

    def save_feedback(self, user_id: int, ai_character: dict, rating: str = None, complaint: str = None) -> bool:
        """
        Сохраняет оценку или жалобу на AI персонажа.

        :param user_id: ID пользователя
        :param ai_character: словарь с данными персонажа (name, age, gender, topic)
        :param rating: 'good' или 'bad' (для оценки)
        :param complaint: текст жалобы (для жалобы)
        """
        query = '''
            INSERT INTO ai_feedback (user_id, ai_name, ai_age, ai_gender, topic, rating, is_complaint, complaint_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        return self._execute(query, (
            user_id,
            ai_character.get('name'),
            ai_character.get('age'),
            ai_character.get('gender'),
            ai_character.get('topic'),
            rating,
            1 if complaint else 0,
            complaint
        )) is not None

    def get_feedback_stats(self, ai_name: str = None) -> Dict:
        """
        Возвращает статистику оценок AI.
        Если указан ai_name — только для этого персонажа.
        """
        if ai_name:
            good = self._fetch_one('SELECT COUNT(*) as cnt FROM ai_feedback WHERE ai_name = ? AND rating = "good"', (ai_name,))
            bad = self._fetch_one('SELECT COUNT(*) as cnt FROM ai_feedback WHERE ai_name = ? AND rating = "bad"', (ai_name,))
            complaints = self._fetch_one('SELECT COUNT(*) as cnt FROM ai_feedback WHERE ai_name = ? AND is_complaint = 1', (ai_name,))
        else:
            good = self._fetch_one('SELECT COUNT(*) as cnt FROM ai_feedback WHERE rating = "good"')
            bad = self._fetch_one('SELECT COUNT(*) as cnt FROM ai_feedback WHERE rating = "bad"')
            complaints = self._fetch_one('SELECT COUNT(*) as cnt FROM ai_feedback WHERE is_complaint = 1')

        good_count = good['cnt'] if good else 0
        bad_count = bad['cnt'] if bad else 0
        total = good_count + bad_count

        return {
            'good': good_count,
            'bad': bad_count,
            'complaints': complaints['cnt'] if complaints else 0,
            'total': total,
            'positive_rate': round(good_count / total * 100, 1) if total > 0 else 0
        }

    def get_complaints_by_ai(self, limit: int = 50) -> List[Dict]:
        """Возвращает жалобы на AI с группировкой по персонажам"""
        query = '''
            SELECT ai_name, COUNT(*) as cnt, GROUP_CONCAT(complaint_reason) as reasons
            FROM ai_feedback
            WHERE is_complaint = 1
            GROUP BY ai_name
            ORDER BY cnt DESC
            LIMIT ?
        '''
        return self._fetch_all(query, (limit,))

    # ========== AI СЕССИИ (логгирование) ==========

    def log_session_start(self, user_id: int, character_id: int) -> int:
        """Логирует начало AI сессии. Возвращает ID сессии."""
        query = '''
            INSERT INTO ai_sessions_log (user_id, character_id, started_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        '''
        cursor = self._execute(query, (user_id, character_id))
        return cursor.lastrowid if cursor else 0

    def log_session_end(self, session_id: int, messages_count: int) -> bool:
        """Логирует завершение AI сессии."""
        query = 'UPDATE ai_sessions_log SET ended_at = CURRENT_TIMESTAMP, messages_count = ? WHERE id = ?'
        return self._execute(query, (messages_count, session_id)) is not None

    # ========== УПРАВЛЕНИЕ МОДЕЛЯМИ ИЗ АДМИНКИ ==========

    def get_all_models(self) -> List[Dict]:
        """Возвращает список всех AI моделей"""
        return self._fetch_all('SELECT * FROM ai_models ORDER BY priority DESC')

    def update_model(self, model_id: int, **kwargs) -> bool:
        """Обновляет параметры модели (температура, токены и т.д.)"""
        allowed_fields = ['name', 'provider', 'is_active', 'is_free',
                        'max_tokens', 'temperature', 'top_p',
                        'frequency_penalty', 'presence_penalty', 'priority']

        fields = []
        values = []
        for key, value in kwargs.items():
            if key in allowed_fields:
                fields.append(f"{key} = ?")
                values.append(value)

        if not fields:
            return False

        values.append(model_id)
        query = f'UPDATE ai_models SET {", ".join(fields)} WHERE id = ?'
        return self._execute(query, tuple(values)) is not None

    def delete_model(self, model_id: int) -> bool:
        """Удаляет модель"""
        return self._execute('DELETE FROM ai_models WHERE id = ?', (model_id,)) is not None

    # ========== УПРАВЛЕНИЕ ПЕРСОНАЖАМИ ИЗ АДМИНКИ ==========

    def get_all_characters(self, include_inactive: bool = False) -> List[Dict]:
        """Возвращает список всех AI персонажей"""
        if include_inactive:
            return self._fetch_all('SELECT * FROM ai_characters ORDER BY topic, gender')
        else:
            return self._fetch_all('SELECT * FROM ai_characters WHERE is_active = 1 ORDER BY topic, gender')

    def get_character_by_id(self, character_id: int) -> Optional[Dict]:
        """Возвращает персонажа по ID"""
        return self._fetch_one('SELECT * FROM ai_characters WHERE id = ?', (character_id,))

    def create_character(self, name: str, age: int, gender: str, topic: str,
                        prompt: str, traits: str = '', style: str = '',
                        rules: str = '') -> int:
        """Создаёт нового AI персонажа"""
        query = '''
            INSERT INTO ai_characters (name, age, gender, topic, prompt, traits, style, rules, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
        '''
        cursor = self._execute(query, (name, age, gender, topic, prompt, traits, style, rules))
        return cursor.lastrowid if cursor else 0

    def update_character(self, character_id: int, **kwargs) -> bool:
        """Обновляет данные персонажа"""
        allowed_fields = ['name', 'age', 'gender', 'topic', 'prompt',
                        'traits', 'style', 'rules', 'is_active']

        fields = []
        values = []
        for key, value in kwargs.items():
            if key in allowed_fields:
                fields.append(f"{key} = ?")
                values.append(value)

        if not fields:
            return False

        values.append(character_id)
        query = f'UPDATE ai_characters SET {", ".join(fields)} WHERE id = ?'
        return self._execute(query, tuple(values)) is not None

    def delete_character(self, character_id: int, hard: bool = False) -> bool:
        """Удаляет персонажа (hard=True — полностью, иначе деактивирует)"""
        if hard:
            return self._execute('DELETE FROM ai_characters WHERE id = ?', (character_id,)) is not None
        else:
            return self._execute('UPDATE ai_characters SET is_active = 0 WHERE id = ?', (character_id,)) is not None

    # ========== НАСТРОЙКИ AI (глобальные) ==========

    def get_ai_settings(self) -> Dict:
        """Возвращает глобальные настройки AI"""
        rows = self._fetch_all('SELECT key, value FROM ai_settings')
        return {row['key']: row['value'] for row in rows}

    def set_ai_setting(self, key: str, value: str) -> bool:
        """Устанавливает глобальную настройку AI"""
        query = 'INSERT OR REPLACE INTO ai_settings (key, value) VALUES (?, ?)'
        return self._execute(query, (key, value)) is not None
