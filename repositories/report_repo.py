# repositories/report_repo.py
"""
Репозиторий для работы с жалобами.
Таблицы: reports
"""

import logging
from typing import Optional, Dict, List

from .base_repo import BaseRepo

logger = logging.getLogger(__name__)


class ReportRepo(BaseRepo):
    """Репозиторий жалоб"""

    async def _ensure_tables(self):
        """Создаёт таблицу для жалоб, если её нет"""
        # async with await self._get_connection() as db:
        db = await self._get_connection()
        await db.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reporter_id INTEGER,
                reported_id INTEGER,
                reason TEXT,
                chat_token TEXT,
                status TEXT DEFAULT 'pending',
                admin_id INTEGER,
                admin_notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                resolved_at TEXT,
                FOREIGN KEY (reporter_id) REFERENCES users(user_id),
                FOREIGN KEY (reported_id) REFERENCES users(user_id)
            )
        ''')

        await db.execute('CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_reports_reporter ON reports(reporter_id)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_reports_reported ON reports(reported_id)')

        await db.commit()
        logger.info("✅ Таблица жалоб создана/проверена")

    async def create_report(self, reporter_id: int, reported_id: int, reason: str, chat_token: str = None) -> int:
        """Создаёт новую жалобу"""
        query = '''
            INSERT INTO reports (reporter_id, reported_id, reason, chat_token, status, created_at)
            VALUES (?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
        '''
        cursor = await self._execute(query, (reporter_id, reported_id, reason, chat_token))
        return cursor.lastrowid if cursor else 0

    async def get_report(self, report_id: int) -> Optional[Dict]:
        """Возвращает жалобу по ID"""
        return await self._fetch_one('SELECT * FROM reports WHERE id = ?', (report_id,))

    async def get_pending_reports(self, limit: int = 50) -> List[Dict]:
        """Возвращает список непроверенных жалоб"""
        query = 'SELECT * FROM reports WHERE status = "pending" ORDER BY created_at ASC LIMIT ?'
        return await self._fetch_all(query, (limit,))

    async def get_reports_by_user(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Возвращает жалобы, связанные с пользователем"""
        query = '''
            SELECT * FROM reports
            WHERE reporter_id = ? OR reported_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        '''
        return await self._fetch_all(query, (user_id, user_id, limit))

    async def resolve_report(self, report_id: int, admin_id: int, action: str, notes: str = '') -> bool:
        """Разрешает жалобу"""
        query = '''
            UPDATE reports
            SET status = ?, admin_id = ?, admin_notes = ?, resolved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        '''
        return await self._execute(query, (action, admin_id, notes, report_id)) is not None

    async def get_reports_count(self, status: str = None) -> int:
        """Возвращает количество жалоб по статусу"""
        if status:
            row = await self._fetch_one('SELECT COUNT(*) as cnt FROM reports WHERE status = ?', (status,))
        else:
            row = await self._fetch_one('SELECT COUNT(*) as cnt FROM reports')
        return row['cnt'] if row else 0
