# utils/init_db.py
"""
Скрипт для инициализации БД (создание всех таблиц).
Запускать перед первым запуском бота.
"""

import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_PATH
from repositories.user_repo import UserRepo
from repositories.chat_repo import ChatRepo
from repositories.report_repo import ReportRepo
from repositories.ai_repo import AIRepo


def init_database():
    """Создаёт все таблицы в БД"""

    print(f"Инициализация БД: {DB_PATH}")

    # Создаём папку для БД, если её нет
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Инициализируем репозитории (они сами создадут таблицы)
    user_repo = UserRepo(str(DB_PATH))
    chat_repo = ChatRepo(str(DB_PATH))
    report_repo = ReportRepo(str(DB_PATH))
    ai_repo = AIRepo(str(DB_PATH))

    print("✅ Все таблицы созданы")

    # Проверяем
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    print("\n📋 Созданные таблицы:")
    for table in tables:
        print(f"  - {table[0]}")
    conn.close()


if __name__ == "__main__":
    init_database()
