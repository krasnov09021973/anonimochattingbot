"""
Репозиторий для работы с темами общения.
Версия 4.3.0 (Авто-наполнение базовыми данными при первом старте)
"""

import logging
from typing import List, Dict, Optional
from .base_repo import BaseRepo

logger = logging.getLogger(__name__)

class TopicRepo(BaseRepo):
    """Репозиторий для динамического управления темами"""

    async def _ensure_tables(self):
        """Создаёт таблицы для тем и наполняет их базовыми данными, если база пуста"""
        # async with await self._get_connection() as db:
        db = await self._get_connection()
        # 1. СОЗДАЕМ ГЛАВНУЮ ТАБЛИЦУ ТЕМ (Каркас)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS topics (
                topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,          -- Системное имя темы (например, 'gaming')
                emoji TEXT DEFAULT '🎯',            -- Эмодзи темы
                is_active INTEGER DEFAULT 1         -- Активна ли тема в боте
            )
        ''')

        # 2. СОЗДАЕМ ТАБЛИЦУ МУЛЬТИЯЗЫЧНЫХ ПЕРЕВОДОВ И ОПИСАНИЙ ТЕМ
        await db.execute('''
            CREATE TABLE IF NOT EXISTS topic_translations (
                topic_id INTEGER,
                lang TEXT NOT NULL,                 -- Код языка ('ru', 'en')
                title TEXT NOT NULL,                -- Красивое название ('Гейминг')
                description TEXT,                   -- Описание темы для админки
                PRIMARY KEY (topic_id, lang),
                FOREIGN KEY (topic_id) REFERENCES topics(topic_id) ON DELETE CASCADE
            )
        ''')
        await db.commit()

        # 3. ПЕРВОНАЧАЛЬНОЕ НАПОЛНЕНИЕ (СИД БАЗЫ ДАННЫХ)
        # Проверяем, есть ли вообще темы в базе данных
        cursor = await db.execute('SELECT COUNT(*) AS cnt FROM topics')
        row = await cursor.fetchone()

        # Если в таблице 0 записей — значит, база данных чистая, нужно накатить дефолтные темы!
        if row and row[0] == 0:
            logger.info("📦 База данных тем пуста. Запуск авто-наполнения дефолтными интересами...")

            # Задаем массив базовых тем (Системное имя, Эмодзи, Русское название, Русское описание)
            default_topics = [
                ("gaming", "🎮", "Гейминг", "Обсуждение видеоигр, консолей, ПК и новинок игровой индустрии."),
                ("movies", "🎬", "Кино и Сериалы", "Для любителей кинематографа. Обсуждаем фильмы, сериалы, аниме и теории."),
                ("music", "🎵", "Музыка", "Делитесь любимыми треками, группами, жанрами и обсуждайте концерты."),
                ("loneliness", "🌌", "Одиночество","Разговоры по душам, философия, поиск 'смысла жизни' и друзей 'по несчастью'"),
                ("relationship", "❤️", "Отношения", "Разговоры о любви, дружбе, психологии отношений и жизненном опыте."),
                ("flirt", "💘", "Флуд и Флирт", "Простое легкое общение обо всем на свете без строгих рамок.")
            ]

            for sys_name, emoji, title, desc in default_topics:
                # А. Записываем каркас темы в таблицу topics
                # Используем INSERT OR IGNORE на всякий случай
                cursor_insert = await db.execute(
                    'INSERT OR IGNORE INTO topics (name, emoji) VALUES (?, ?)',
                    (sys_name, emoji)
                )
                # Вытаскиваем ID, который SQLite только что присвоил этой теме (автоинкремент)
                inserted_topic_id = cursor_insert.lastrowid

                # Б. Если тема успешно создалась, сразу пишем её перевод на русский язык по умолчанию
                if inserted_topic_id:
                    await db.execute('''
                        INSERT INTO topic_translations (topic_id, lang, title, description)
                        VALUES (?, 'ru', ?, ?)
                    ''', (inserted_topic_id, title, desc))

            # Фиксируем все изменения на жесткий диск
            await db.commit()
            logger.info("✅ Базовые темы успешно импортированы в базу данных на языке RU")
        else:
            logger.info("✅ Таблицы тем верифицированы, базовое наполнение не требуется")


    # =====================================================================
    # МЕТОД ПОЛУЧЕНИЯ ТЕМ ДЛЯ МЕНЮ БОТА (ПОДТЯГИВАЕТ НУЖНЫЙ ЯЗЫК)
    # =====================================================================
    async def get_all_topics_with_lang(self, lang: str) -> List[Dict]:
        """
        Запрашивает из БД список всех активных тем, автоматически подтягивая
        нужный перевод названия и описания на языке пользователя.
        """
        query = '''
            SELECT
                t.topic_id,
                t.name AS sys_name,
                t.emoji,
                COALESCE(tr.title, t.name) AS title,
                COALESCE(tr.description, '') AS description
            FROM topics t
            -- Присоединяем переводы строго по текущему языку сессии пользователя
            LEFT JOIN topic_translations tr ON t.topic_id = tr.topic_id AND tr.lang = ?
            WHERE t.is_active = 1
            ORDER BY title ASC
        '''
        return await self._fetch_all(query, (lang,))

    async def get_topic_by_id(self, topic_id: int) -> Optional[Dict]:
        """
        Находит emoji и системное название темы по её числовому ID.
        Используется фоновым конвейером для маскировки и приветствий.
        """
        query = 'SELECT emoji, name FROM topics WHERE topic_id = ?'
        return await self._fetch_one(query, (topic_id,))
