# utils/migrate_db.py
"""
Скрипт для миграции данных из старой БД в новую структуру.
Запускать один раз при переходе на новую версию.
"""

import sqlite3
import logging
from pathlib import Path

# Пути к базам данных
OLD_DB_PATH = Path(__file__).parent.parent / 'data' / 'anon_chat.db'
NEW_DB_PATH = Path(__file__).parent.parent / 'data' / 'anon_chat_new.db'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate():
    """Выполняет миграцию данных"""

    if not OLD_DB_PATH.exists():
        logger.error(f"Старая БД не найдена: {OLD_DB_PATH}")
        return

    logger.info(f"Миграция из {OLD_DB_PATH} в {NEW_DB_PATH}")

    # Подключаемся к старой БД
    old_conn = sqlite3.connect(OLD_DB_PATH)
    old_conn.row_factory = sqlite3.Row
    old_cursor = old_conn.cursor()

    # Создаём новую БД
    new_conn = sqlite3.connect(NEW_DB_PATH)
    new_cursor = new_conn.cursor()

    # === 1. Создаём таблицы в новой БД ===
    create_tables(new_cursor)

    # === 2. Переносим пользователей ===
    logger.info("Перенос пользователей...")
    old_cursor.execute('SELECT * FROM users')
    users = old_cursor.fetchall()

    for user in users:
        # Преобразуем Row в dict для удобства
        user_dict = dict(user)

        new_cursor.execute('''
            INSERT OR REPLACE INTO users (
                user_id, username, chat_name, age, gender, reputation,
                is_premium, premium_until, is_banned, ban_reason,
                total_chats, total_messages, total_searches,
                registered_at, last_activity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_dict.get('user_id'),
            user_dict.get('username'),
            user_dict.get('chat_name'),
            user_dict.get('age'),
            user_dict.get('gender', 'unknown'),
            user_dict.get('reputation', 25),
            user_dict.get('is_premium', 0),
            user_dict.get('premium_until'),
            user_dict.get('is_banned', 0),
            user_dict.get('ban_reason'),
            user_dict.get('chats_count', 0),
            user_dict.get('total_messages_sent', 0),
            user_dict.get('searches_count', 0),
            user_dict.get('registered_at'),
            user_dict.get('last_activity')
        ))

    logger.info(f"Перенесено пользователей: {len(users)}")

    # === 3. Переносим фото пользователей ===
    logger.info("Перенос фото...")
    old_cursor.execute('SELECT * FROM user_photos')
    photos = old_cursor.fetchall()

    for photo in photos:
        new_cursor.execute('''
            INSERT INTO user_photos (user_id, photo_file_id, position, created_at)
            VALUES (?, ?, ?, ?)
        ''', (
            photo['user_id'],
            photo['photo_file_id'],
            photo.get('position', 0),
            photo.get('created_at')
        ))

    logger.info(f"Перенесено фото: {len(photos)}")

    # === 4. Переносим темы пользователей ===
    logger.info("Перенос тем...")
    old_cursor.execute('SELECT * FROM user_topics')
    topics = old_cursor.fetchall()

    for topic in topics:
        # Преобразуем Row в dict для удобства
        topic_dict = dict(topic)

        new_cursor.execute('''
            INSERT OR REPLACE INTO user_topics (user_id, topic_id, selected_at)
            VALUES (?, ?, ?)
        ''', (
            topic_dict.get('user_id'),
            topic_dict.get('topic_id'),
            topic_dict.get('selected_at')
        ))

    logger.info(f"Перенесено тем: {len(topics)}")

    # === 5. Переносим историю чатов ===
    logger.info("Перенос истории чатов...")
    old_cursor.execute('SELECT * FROM chat_history')
    histories = old_cursor.fetchall()

    for hist in histories:
        hist_dict = dict(hist)

        new_cursor.execute('''
            INSERT INTO chat_history (
                id, user1_id, user2_id, started_at, ended_at,
                duration_seconds, user1_left_first
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            hist_dict.get('chat_id'),
            hist_dict.get('user1_id'),
            hist_dict.get('user2_id'),
            hist_dict.get('started_at'),
            hist_dict.get('ended_at'),
            hist_dict.get('duration_seconds', 0),
            hist_dict.get('user1_left_first', 1)
        ))

    logger.info(f"Перенесено историй: {len(histories)}")

    # === 6. Переносим жалобы ===
    logger.info("Перенос жалоб...")
    old_cursor.execute('SELECT * FROM reports')
    reports = old_cursor.fetchall()

    for report in reports:
        report_dict = dict(report)
        new_cursor.execute('''
            INSERT INTO reports (
                id, reporter_id, reported_id, reason, chat_token, status,
                admin_id, admin_notes, created_at, resolved_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            report_dict.get('report_id'),
            report_dict.get('reporter_id'),
            report_dict.get('reported_id'),
            report_dict.get('reason', ''),
            report_dict.get('chat_token'),
            report_dict.get('status', 'pending'),
            report_dict.get('admin_id'),
            report_dict.get('admin_notes'),
            report_dict.get('created_at'),
            report_dict.get('resolved_at')
        ))

    logger.info(f"Перенесено жалоб: {len(reports)}")

    # === 7. Переносим AI фидбек ===
    logger.info("Перенос AI фидбека...")
    old_cursor.execute('SELECT * FROM ai_feedback')
    ai_feedbacks = old_cursor.fetchall()

    for fb in ai_feedbacks:
        fb_dict = dict(fb)
        new_cursor.execute('''
            INSERT INTO ai_feedback (
                user_id, ai_name, ai_age, ai_gender, topic,
                rating, is_complaint, complaint_reason, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            fb_dict.get('user_id'),
            fb_dict.get('ai_name'),
            fb_dict.get('ai_age'),
            fb_dict.get('ai_gender'),
            fb_dict.get('topic'),
            fb_dict.get('rating'),
            fb_dict.get('is_complaint', 0),
            fb_dict.get('complaint_reason'),
            fb['created_at']
        ))

    logger.info(f"Перенесено AI фидбеков: {len(ai_feedbacks)}")

    # Сохраняем изменения
    new_conn.commit()

    # Закрываем соединения
    old_conn.close()
    new_conn.close()

    logger.info(f"✅ Миграция завершена! Новая БД: {NEW_DB_PATH}")
    logger.info("❗ Не забудьте переименовать файлы: anon_chat.db -> anon_chat.db.old, anon_chat_new.db -> anon_chat.db")


def create_tables(cursor):
    """Создаёт таблицы в новой БД"""

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

    # Таблица фото
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
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        )
    ''')

    # Таблица тем
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS topics (
            topic_id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            emoji TEXT,
            description TEXT
        )
    ''')

    # История чатов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER,
            user2_id INTEGER,
            started_at TIMESTAMP,
            ended_at TIMESTAMP,
            duration_seconds INTEGER,
            user1_left_first BOOLEAN,
            FOREIGN KEY (user1_id) REFERENCES users(user_id),
            FOREIGN KEY (user2_id) REFERENCES users(user_id)
        )
    ''')

    # Жалобы
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_id INTEGER,
            reported_id INTEGER,
            reason TEXT,
            chat_token TEXT,
            status TEXT DEFAULT 'pending',
            admin_id INTEGER,
            admin_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            resolved_at TIMESTAMP,
            FOREIGN KEY (reporter_id) REFERENCES users(user_id),
            FOREIGN KEY (reported_id) REFERENCES users(user_id)
        )
    ''')

    # AI фидбек
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

    # Инициализируем темы
    init_topics(cursor)


def init_topics(cursor):
    """Заполняет таблицу тем"""
    topics = [
        (1, 'Ролевые игры', '🎭', 'Ролевые игры, D&D, живые действия'),
        (2, 'Мемы', '😂', 'Мемы, юмор, приколы'),
        (3, 'Одиночество', '🌌', 'Разговоры по душам, философия'),
        (4, 'Игры', '🎮', 'Видеоигры, настолки, киберспорт'),
        (5, 'Флирт', '💘', 'Флирт, знакомства, отношения'),
        (6, 'Путешествия', '✈️', 'Туризм, страны, культура'),
        (7, 'IT. Компьютеры', '💻', 'Программирование, гаджеты, технологии'),
        (8, 'Музыка', '🎵', 'Любая музыка, концерты, артисты'),
        (9, 'Авто', '🚗', 'Машины, тюнинг, гонки'),
        (10, 'Аниме', '🇯🇵', 'Аниме, манга, культура Японии'),
        (11, 'Фильмы', '🎬', 'Кино, сериалы, документальное'),
        (12, 'Питомцы', '🐕', 'Домашние животные, уход, истории'),
        (13, 'Книги', '📚', 'Литература, аудиокниги, писатели'),
        (14, 'Спорт', '⚽', 'Футбол, хоккей, MMA, фитнес'),
    ]

    for topic in topics:
        cursor.execute('''
            INSERT OR REPLACE INTO topics (topic_id, name, emoji, description)
            VALUES (?, ?, ?, ?)
        ''', topic)


if __name__ == "__main__":
    migrate()
