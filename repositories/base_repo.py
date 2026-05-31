# repositories/base_repo.py
"""
Базовый репозиторий с асинхронными методами.
"""

import aiosqlite
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any

logger = logging.getLogger(__name__)


class BaseRepo:
    """Базовый класс для всех репозиториев"""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    async def _execute(self, query: str, params: tuple = ()) -> Optional[aiosqlite.Cursor]:
        """Выполняет INSERT/UPDATE/DELETE"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                conn.row_factory = aiosqlite.Row
                cursor = await conn.execute(query, params)
                await conn.commit()
                return cursor
        except aiosqlite.Error as e:
            logger.error(f"Ошибка БД: {e}\nЗапрос: {query}\nПараметры: {params}")
            return None

    async def _fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
        """Выполняет SELECT и возвращает одну строку"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                conn.row_factory = aiosqlite.Row
                cursor = await conn.execute(query, params)
                row = await cursor.fetchone()
                return dict(row) if row else None
        except aiosqlite.Error as e:
            logger.error(f"Ошибка БД: {e}\nЗапрос: {query}")
            return None

    async def _fetch_all(self, query: str, params: tuple = ()) -> List[Dict]:
        """Выполняет SELECT и возвращает все строки"""
        try:
            async with aiosqlite.connect(self.db_path) as conn:
                conn.row_factory = aiosqlite.Row
                cursor = await conn.execute(query, params)
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
        except aiosqlite.Error as e:
            logger.error(f"Ошибка БД: {e}\nЗапрос: {query}")
            return []

    async def _get_connection(self) -> aiosqlite.Connection:
        """Возвращает асинхронное соединение с БД"""
        conn = await aiosqlite.connect(self.db_path)
        conn.row_factory = aiosqlite.Row
        return conn

    # async def _execute(self, query: str, params: tuple = ()) -> Optional[aiosqlite.Cursor]:
    #     """Выполняет запрос INSERT/UPDATE/DELETE"""
    #     try:
    #         async with await self._get_connection() as conn:
    #             cursor = await conn.execute(query, params)
    #             await conn.commit()
    #             return cursor
    #     except aiosqlite.Error as e:
    #         logger.error(f"Ошибка БД: {e}\nЗапрос: {query}\nПараметры: {params}")
    #         return None
    #
    # async def _fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict]:
    #     """Выполняет SELECT и возвращает одну строку"""
    #     try:
    #         async with await self._get_connection() as conn:
    #             cursor = await conn.execute(query, params)
    #             row = await cursor.fetchone()
    #             return dict(row) if row else None
    #     except aiosqlite.Error as e:
    #         logger.error(f"Ошибка БД: {e}\nЗапрос: {query}")
    #         return None
    #
    # async def _fetch_all(self, query: str, params: tuple = ()) -> List[Dict]:
    #     """Выполняет SELECT и возвращает все строки"""
    #     try:
    #         async with await self._get_connection() as conn:
    #             cursor = await conn.execute(query, params)
    #             rows = await cursor.fetchall()
    #             return [dict(row) for row in rows]
    #     except aiosqlite.Error as e:
    #         logger.error(f"Ошибка БД: {e}\nЗапрос: {query}")
    #         return []
