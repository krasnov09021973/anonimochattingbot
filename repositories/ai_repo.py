# repositories/ai_repo.py
"""
Репозиторий для работы с AI.
Таблицы: ai_characters, ai_models, ai_feedback, ai_sessions_log
"""

import logging
from typing import Optional, Dict, List

from .base_repo import BaseRepo

logger = logging.getLogger(__name__)


class AIRepo(BaseRepo):
    """Репозиторий для AI"""

    async def _ensure_tables(self):
        """Создаёт все таблицы для AI"""
        # async with await self._get_connection() as db:
        db = await self._get_connection()
        # AI персонажи
        # 1. СТАТИЧЕСКАЯ ТАБЛИЦА (Управляет структурой сущностей и фильтром пола)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ai_characters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gender TEXT NOT NULL,         -- 'male' / 'female'
                min_age INTEGER DEFAULT 18,
                max_age INTEGER DEFAULT 30,
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL      -- Храним ISO-дату
            );
        ''')

        # 2. ТАБЛИЦА ЛОКАЛИЗАЦИИ (Хранит промпты, топики и имена под каждый язык)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ai_character_translations (
                character_id INTEGER NOT NULL,
                lang TEXT NOT NULL,           -- 'ru', 'en' и т.д.
                topic TEXT NOT NULL,          -- Должно совпадать с именем в таблице topics
                names TEXT NOT NULL,          -- JSON-массив имен: '["Алина", "Катя"]'
                traits TEXT,                  -- Короткое описание характера
                style TEXT,                   -- Описание манеры общения
                rules TEXT,                   -- Правила поведения бота
                prompt TEXT,                  -- Дополнительный системный оверрайд (если нужен)
                PRIMARY KEY (character_id, lang),
                FOREIGN KEY (character_id) REFERENCES ai_characters(id) ON DELETE CASCADE
            );
        ''')
        # AI модели
        await db.execute('''
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
        await db.execute('''
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
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # AI сессии (лог)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ai_sessions_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                character_id INTEGER,
                messages_count INTEGER,
                started_at TEXT,
                ended_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (character_id) REFERENCES ai_characters(id)
            )
        ''')

        # Настройки AI
        await db.execute('''
            CREATE TABLE IF NOT EXISTS ai_settings (
                key TEXT PRIMARY KEY,
                value TEXT,
                description TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Индексы
        await db.execute('CREATE INDEX IF NOT EXISTS idx_ai_feedback_user ON ai_feedback(user_id)')

        # Дописываем автозаполнение ключа в самый конец метода _ensure_tables() в ai_repo.py
        await db.execute('''
            INSERT OR IGNORE INTO ai_settings (key, value, description)
            VALUES (
                'general_chat_rules',
                'ВАЖНОЕ СИСТЕМНОЕ ПРАВИЛО: Сейчас ты общаешься в АНОНИМНОМ СЛУЧАЙНОМ ЧАТЕ обо всем подряд. Твой собеседник НЕ выбирал конкретную тему диалога. Общайся как обычный, живой и легкий на подъем человек. Отвечай короткими, разговорными фразами (1-3 предложения), пиши естественно. Ты можешь плавно упоминать свои интересы и характер, но НЕ зацикливайся на них, если собеседник говорит о другом. Категорически запрещено говорить, что ты искусственный интеллект или языковая модель.\n\n',
                'Над-инструкция для маскировки ИИ-персонажей в обычном поиске'
            )
        ''')


        await db.commit()
        logger.info("✅ Таблицы AI созданы/проверены")

    # ========== ПЕРСОНАЖИ ==========
    # =====================================================================
    # НОВЫЙ МЕТОД: ПОДБОР ОБЩЕГО ИИ ДЛЯ ОБЫЧНОГО ПОИСКА (БЕЗ ТЕМ)
    # =====================================================================
    async def get_general_character(self) -> Optional[Dict]:
        """
        Находит одного случайного активного ИИ-персонажа, у которого
        поле темы (topic) равно NULL или пустой строке. Это общий собеседник.

        Выход: Словарь с данными персонажа или None
        """
        query = '''
            SELECT id, name, prompt, gender
            FROM ai_characters
            WHERE is_active = 1
              AND (topic IS NULL OR topic = '')
            ORDER BY RANDOM()
            LIMIT 1
        '''
        # Вызываем встроенный метод пошагового чтения одной строки
        return await self._fetch_one(query)

    # =====================================================================
    # НОВЫЙ МЕТОД: ПОДБОР ИИ ПО ТЕМАМ ПОЛЬЗОВАТЕЛЯ (ДЛЯ ТЕМАТИЧЕСКОГО ПОИСКА)
    # =====================================================================
    async def get_character_by_user_topics(self, user_topic_names: List[str]) -> Optional[Dict]:
        """
        Находит одного случайного ИИ-персонажа, тема которого совпадает
        хотя бы с одной из тем, переданных в списке.

        Вход: user_topic_names — список текстовых названий тем (например, ['gaming', 'movies'])
        Выход: Словарь с данными совпавшего персонажа или None
        """
        if not user_topic_names:
            return None

        # Создаем знаки вопросов для SQL-инструкции IN (?, ?, ...)
        placeholders = ', '.join('?' for _ in user_topic_names)

        query = f'''
            SELECT id, name, prompt, topic as topic_name
            FROM ai_characters
            WHERE is_active = 1
              AND topic IN ({placeholders})   -- Ищем совпадение по текстовому полю темы
            ORDER BY RANDOM()
            LIMIT 1
        '''

        # Передаем список названий тем в качестве параметров запроса
        return await self._fetch_one(query, tuple(user_topic_names))

    # =====================================================================

    async def create_ai_session(self, chat_token: str, user_id: int, character_id: int) -> bool:
        """
        Создает запись о начале сессии с ИИ в таблице логов.
        Чистый SQL инкапсулирован внутри репозитория!
        """
        query = """
            INSERT INTO ai_sessions_log (chat_token, user_id, character_id, is_active, started_at)
            VALUES (?, ?, ?, 1, datetime('now'))
        """
        cursor = await self._execute(query, (chat_token, user_id, character_id))
        return cursor is not None

    # =====================================================================

    async def get_character_by_topic(self, topic_name: str, gender_filter: str, user_lang: str) -> list:
        """
        Ищет персонажей по имени темы, фильтру пола и языку пользователя через JOIN.
        Использует базовый метод _fetch_all, возвращающий готовые dict.
        """
        query = """
            SELECT c.id, c.gender, c.min_age, c.max_age,
                   t.topic, t.names, t.traits, t.style, t.rules, t.prompt
            FROM ai_characters c
            JOIN ai_character_translations t ON c.id = t.character_id
            WHERE LOWER(t.topic) = LOWER(?) AND LOWER(t.lang) = LOWER(?) AND c.is_active = 1
        """
        params = [topic_name, user_lang.lower()]

        if gender_filter != "normal":
            query += " AND c.gender = ?"
            params.append(gender_filter)

        # _fetch_all сам вернет список готовых словарей или пустой список [] в случае ошибки/пустоты
        return await self._fetch_all(query, tuple(params))

    async def get_all_characters(self, gender_filter: str, user_lang: str) -> list:
        """
        Выгребает всех доступных персонажей нужного языка для обычного случайного поиска.
        Использует базовый метод _fetch_all.
        """
        query = """
            SELECT c.id, c.gender, c.min_age, c.max_age,
                   t.topic, t.names, t.traits, t.style, t.rules, t.prompt
            FROM ai_characters c
            JOIN ai_character_translations t ON c.id = t.character_id
            WHERE LOWER(t.lang) = LOWER(?) AND c.is_active = 1
        """
        params = [user_lang.lower()]

        if gender_filter != "normal":
            query += " AND c.gender = ?"
            params.append(gender_filter)

        return await self._fetch_all(query, tuple(params))

    async def get_active_characters(self) -> List[Dict]:
        """Возвращает список активных AI персонажей"""
        query = 'SELECT * FROM ai_characters WHERE is_active = 1'
        return await self._fetch_all(query)

    async def get_character_by_id(self, character_id: int) -> Optional[Dict]:
        """Возвращает персонажа по ID"""
        return await self._fetch_one('SELECT * FROM ai_characters WHERE id = ?', (character_id,))

    async def add_character(self, gender: str, topic: str, name: str, traits: str = '', style: str = '', rules: str = '') -> int:
        """Добавляет нового AI персонажа"""
        query = '''
            INSERT INTO ai_characters (gender, topic, name, traits, style, rules, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        '''
        cursor = await self._execute(query, (gender, topic, name, traits, style, rules))
        return cursor.lastrowid if cursor else 0

    async def update_character(self, character_id: int, **kwargs) -> bool:
        """Обновляет данные персонажа"""
        allowed = ['name', 'gender', 'topic', 'traits', 'style', 'rules', 'prompt', 'is_active', 'min_age', 'max_age']
        fields = [f"{k} = ?" for k in kwargs if k in allowed]
        if not fields:
            return False

        values = [kwargs[k] for k in kwargs if k in allowed]
        values.append(character_id)
        query = f'UPDATE ai_characters SET {", ".join(fields)} WHERE id = ?'
        return await self._execute(query, tuple(values)) is not None

    # ========== МОДЕЛИ ==========

    async def get_active_model(self) -> Optional[Dict]:
        """Возвращает активную модель с наивысшим приоритетом"""
        query = 'SELECT * FROM ai_models WHERE is_active = 1 ORDER BY priority ASC LIMIT 1'
        return await self._fetch_one(query)

    async def get_model_by_name(self, name: str) -> Optional[Dict]:
        """Возвращает модель по имени"""
        return await self._fetch_one('SELECT * FROM ai_models WHERE name = ?', (name,))

    async def set_active_model(self, model_id: int) -> bool:
        """Устанавливает активную модель (снимает активность с остальных)"""
        await self._execute('UPDATE ai_models SET is_active = 0')
        return await self._execute('UPDATE ai_models SET is_active = 1 WHERE id = ?', (model_id,)) is not None

    async def add_model(self, name: str, provider: str, **kwargs) -> int:
        """Добавляет новую AI модель"""
        query = '''
            INSERT INTO ai_models (name, provider, max_tokens, temperature, top_p, frequency_penalty, presence_penalty)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        cursor = await self._execute(query, (
            name, provider,
            kwargs.get('max_tokens', 400),
            kwargs.get('temperature', 0.9),
            kwargs.get('top_p', 0.9),
            kwargs.get('frequency_penalty', 0.3),
            kwargs.get('presence_penalty', 0.2)
        ))
        return cursor.lastrowid if cursor else 0

    # ========== НАСТРОЙКИ ==========

    async def get_settings(self) -> Dict:
        """Возвращает все настройки AI"""
        rows = await self._fetch_all('SELECT key, value FROM ai_settings')
        return {row['key']: row['value'] for row in rows}

    async def get_setting(self, key: str, default: str = None) -> str:
        """Возвращает настройку по ключу"""
        row = await self._fetch_one('SELECT value FROM ai_settings WHERE key = ?', (key,))
        return row['value'] if row else default

    async def set_setting(self, key: str, value: str) -> bool:
        """Устанавливает настройку"""
        query = 'INSERT OR REPLACE INTO ai_settings (key, value) VALUES (?, ?)'
        return await self._execute(query, (key, value)) is not None

    # ========== ФИДБЕК ==========

    # ========== ФИДБЕК (ОЦЕНКИ И ЖАЛОБЫ) ==========

    async def save_feedback(self, user_id: int, ai_name: str, ai_age: int, ai_gender: str, topic: str, rating: str = None, complaint: str = None) -> bool:
        """
        Сохраняет оценку (лайк/дизлайк) или текстовую жалобу на AI персонажа.
        Каждая строчка снабжена комментариями для понимания структуры.
        """
        # Превращаем наличие текста жалобы в числовой флаг (True/False -> 1/0) для SQLite
        is_complaint = 1 if complaint else 0

        query = '''
            INSERT INTO ai_feedback (user_id, ai_name, ai_age, ai_gender, topic, rating, is_complaint, complaint_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        # Выполняем асинхронную запись в файл БД через метод базового репозитория
        return await self._execute(query, (user_id, ai_name, ai_age, ai_gender, topic, rating, is_complaint, complaint)) is not None


    async def get_feedback_stats(self, ai_name: str = None) -> Dict:
        """
        ОПТИМИЗИРОВАНО: Возвращает полную статистику оценок AI.
        Вместо 3-х раздельных тяжелых запросов к диску выполняет всего ОДИН
        эффективный запрос с использованием условной агрегации SQLite.
        """

        # Если передан конкретный ai_name — фильтруем по нему, иначе собираем общую статистику
        if ai_name:
            query = '''
                SELECT
                    SUM(CASE WHEN rating = 'good' THEN 1 ELSE 0 END) AS good_count,
                    SUM(CASE WHEN rating = 'bad' THEN 1 ELSE 0 END) AS bad_count,
                    SUM(CASE WHEN is_complaint = 1 THEN 1 ELSE 0 END) AS complaints_count
                FROM ai_feedback
                WHERE ai_name = ?
            '''
            # Передаем имя персонажа в качестве параметра
            row = await self._fetch_one(query, (ai_name,))
        else:
            query = '''
                SELECT
                    SUM(CASE WHEN rating = 'good' THEN 1 ELSE 0 END) AS good_count,
                    SUM(CASE WHEN rating = 'bad' THEN 1 ELSE 0 END) AS bad_count,
                    SUM(CASE WHEN is_complaint = 1 THEN 1 ELSE 0 END) AS complaints_count
                FROM ai_feedback
            '''
            # Параметры не требуются, так как ищем по всей таблице
            row = await self._fetch_one(query)

        # Вытаскиваем результаты из строки.
        # Если данных в таблице вообще нет (база пустая), SUM вернет None, поэтому подстраховываемся через OR 0.
        good_count = (row['good_count'] if row else 0) or 0
        bad_count = (row['bad_count'] if row else 0) or 0
        complaints_count = (row['complaints_count'] if row else 0) or 0

        # Считаем математику прямо в Python (это мгновенно в ОЗУ)
        total_votes = good_count + bad_count

        # Возвращаем красивую, готовую структуру для нашей админ-панели
        return {
            'good': good_count,
            'bad': bad_count,
            'complaints': complaints_count,
            'total': total_votes,
            # Считаем процент позитивных оценок. Защищаем код от ошибки деления на ноль ZeroDivisionError
            'positive_rate': round(good_count / total_votes * 100, 1) if total_votes > 0 else 0.0
        }

    # Дописываем метод в класс AIRepo в файле ai_repo.py

    async def log_session_start(self, user_id: int, character_id: int) -> bool:
        """
        Записывает старт сессии с ИИ-персонажем в таблицу ai_sessions_log.
        Время начала фиксируется автоматически силами SQLite (CURRENT_TIMESTAMP).
        """
        query = '''
            INSERT INTO ai_sessions_log (user_id, character_id, messages_count, started_at)
            VALUES (?, ?, 0, CURRENT_TIMESTAMP)
        '''
        # Выполняем запрос через вашу стандартную базовую обертку _execute
        return await self._execute(query, (user_id, character_id)) is not None

    async def log_session_end(self, user_id: int) -> bool:
        """
        Фиксирует завершение сессии с ИИ в таблице ai_sessions_log.
        Проставляет время окончания (CURRENT_TIMESTAMP) силами SQLite
        для последней активной сессии пользователя.
        """
        query = '''
            UPDATE ai_sessions_log
            SET ended_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND ended_at IS NULL
        '''
        return await self._execute(query, (user_id,)) is not None
