# repositories/base_repo.py
"""
Базовый класс для всех репозиториев.
Содержит общие методы для работы с БД.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, Any, List, Dict

logger = logging.getLogger(__name__)


class BaseRepo:
    """Базовый класс репозитория. Все репозитории наследуются от него."""

    def __init__(self, db_path: str):
        """
        Инициализация репозитория.

        :param db_path: путь к файлу базы данных SQLite
        """
        self.db_path = db_path
        self._ensure_tables()  # создаём таблицы при инициализации

    def _get_connection(self) -> sqlite3.Connection:
        """
        Возвращает соединение с БД.
        Используем row_factory = sqlite3.Row, чтобы обращаться к колонкам по имени.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self):
        """
        Создаёт все таблицы, если их нет.
        Этот метод будет переопределён в дочерних классах.
        """
        raise NotImplementedError("Дочерний класс должен реализовать _ensure_tables()")

    def _execute(self, query: str, params: tuple = ()) -> Optional[sqlite3.Cursor]:
        """
        Выполняет SQL-запрос с параметрами.
        Используется для INSERT, UPDATE, DELETE.
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return cursor
        except sqlite3.Error as e:
            logger.error(f"Ошибка БД: {e}\nЗапрос: {query}\nПараметры: {params}")
            return None

    def _fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """Выполняет SELECT и возвращает одну строку (в виде словаря)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Ошибка БД: {e}\nЗапрос: {query}")
            return None

    def _fetch_all(self, query: str, params: tuple = ()) -> List[Dict]:
        """Выполняет SELECT и возвращает все строки (в виде списка словарей)"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Ошибка БД: {e}\nЗапрос: {query}")
            return []
