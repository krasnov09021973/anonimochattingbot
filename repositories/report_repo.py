# repositories/report_repo.py
"""
Репозиторий для работы с жалобами.
Таблица: reports
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List

from .base_repo import BaseRepo

logger = logging.getLogger(__name__)


class ReportRepo(BaseRepo):
    """Репозиторий жалоб"""

    def _ensure_tables(self):
        """Создаёт таблицу для жалоб, если её нет"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Таблица жалоб
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

            # Индексы для быстрого поиска
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_reporter ON reports(reporter_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_reports_reported ON reports(reported_id)')

            conn.commit()
            logger.info("✅ Таблица жалоб создана/проверена")

    # ========== СОЗДАНИЕ ЖАЛОБЫ ==========

    def create_report(self, reporter_id: int, reported_id: int, reason: str, chat_token: str = None) -> int:
        """
        Создаёт новую жалобу.

        :param reporter_id: ID жалобщика
        :param reported_id: ID нарушителя
        :param reason: причина жалобы (текст)
        :param chat_token: токен чата (для привязки)
        :return: ID созданной жалобы или 0 при ошибке
        """
        query = '''
            INSERT INTO reports (reporter_id, reported_id, reason, chat_token, status, created_at)
            VALUES (?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
        '''
        cursor = self._execute(query, (reporter_id, reported_id, reason, chat_token))

        if cursor:
            return cursor.lastrowid
        return 0

    # ========== ПОЛУЧЕНИЕ ЖАЛОБ ==========

    def get_report(self, report_id: int) -> Optional[Dict]:
        """Возвращает жалобу по ID"""
        return self._fetch_one('SELECT * FROM reports WHERE id = ?', (report_id,))

    def get_pending_reports(self, limit: int = 50) -> List[Dict]:
        """Возвращает список непроверенных жалоб"""
        query = '''
            SELECT * FROM reports
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT ?
        '''
        return self._fetch_all(query, (limit,))

    def get_reports_by_user(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        Возвращает все жалобы, связанные с пользователем.
        (где он жалобщик или нарушитель)
        """
        query = '''
            SELECT * FROM reports
            WHERE reporter_id = ? OR reported_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        '''
        return self._fetch_all(query, (user_id, user_id, limit))

    def get_reports_by_status(self, status: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        Возвращает жалобы по статусу с пагинацией.
        status: 'pending', 'confirmed', 'rejected'
        """
        query = '''
            SELECT * FROM reports
            WHERE status = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        '''
        return self._fetch_all(query, (status, limit, offset))

    def get_reports_by_chat(self, chat_token: str) -> List[Dict]:
        """Возвращает все жалобы по токену чата"""
        return self._fetch_all('SELECT * FROM reports WHERE chat_token = ?', (chat_token,))

    # ========== ОБРАБОТКА ЖАЛОБ ==========

    def resolve_report(self, report_id: int, admin_id: int, action: str, notes: str = '') -> bool:
        """
        Разрешает жалобу.

        :param report_id: ID жалобы
        :param admin_id: ID админа, который обработал
        :param action: 'confirmed' (подтверждена) или 'rejected' (отклонена)
        :param notes: заметки админа
        """
        query = '''
            UPDATE reports
            SET status = ?, admin_id = ?, admin_notes = ?, resolved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        '''
        return self._execute(query, (action, admin_id, notes, report_id)) is not None

    def confirm_report(self, report_id: int, admin_id: int, notes: str = '') -> bool:
        """Подтверждает жалобу (бан нарушителю)"""
        return self.resolve_report(report_id, admin_id, 'confirmed', notes)

    def reject_report(self, report_id: int, admin_id: int, notes: str = '') -> bool:
        """Отклоняет жалобу (штраф жалобщику за ложную)"""
        return self.resolve_report(report_id, admin_id, 'rejected', notes)

    # ========== СТАТИСТИКА ==========

    def get_reports_count(self, status: str = None) -> int:
        """
        Возвращает количество жалоб.
        Если status указан — только по этому статусу.
        """
        if status:
            row = self._fetch_one('SELECT COUNT(*) as cnt FROM reports WHERE status = ?', (status,))
        else:
            row = self._fetch_one('SELECT COUNT(*) as cnt FROM reports')

        return row['cnt'] if row else 0

    def get_reports_stats(self) -> Dict:
        """Возвращает статистику по жалобам"""
        return {
            'pending': self.get_reports_count('pending'),
            'confirmed': self.get_reports_count('confirmed'),
            'rejected': self.get_reports_count('rejected'),
            'total': self.get_reports_count()
        }

    # ========== ПАГИНАЦИЯ ==========

    def get_reports_by_status_paginated(self, status: str, page: int = 1, limit: int = 20, search: str = "") -> dict:
        """
        Возвращает список жалоб по статусу с пагинацией и поиском.
        status: 'pending', 'confirmed', 'rejected', 'all'
        """
        offset = (page - 1) * limit
        search_filter = f"%{search}%"

        try:
            with self._get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Подсчёт общего количества
                if status == 'all':
                    if search:
                        cursor.execute('''
                            SELECT COUNT(*) FROM reports
                            WHERE report_id LIKE ? OR reason LIKE ? OR reporter_id LIKE ? OR reported_id LIKE ?
                        ''', (search_filter, search_filter, search_filter, search_filter))
                    else:
                        cursor.execute('SELECT COUNT(*) FROM reports')
                else:
                    if search:
                        cursor.execute('''
                            SELECT COUNT(*) FROM reports
                            WHERE status = ? AND (report_id LIKE ? OR reason LIKE ? OR reporter_id LIKE ? OR reported_id LIKE ?)
                        ''', (status, search_filter, search_filter, search_filter, search_filter))
                    else:
                        cursor.execute('SELECT COUNT(*) FROM reports WHERE status = ?', (status,))
                total = cursor.fetchone()[0]

                # Получение списка
                if status == 'all':
                    if search:
                        cursor.execute('''
                            SELECT * FROM reports
                            WHERE report_id LIKE ? OR reason LIKE ? OR reporter_id LIKE ? OR reported_id LIKE ?
                            ORDER BY created_at DESC
                            LIMIT ? OFFSET ?
                        ''', (search_filter, search_filter, search_filter, search_filter, limit, offset))
                    else:
                        cursor.execute('''
                            SELECT * FROM reports
                            ORDER BY created_at DESC
                            LIMIT ? OFFSET ?
                        ''', (limit, offset))
                else:
                    if search:
                        cursor.execute('''
                            SELECT * FROM reports
                            WHERE status = ? AND (report_id LIKE ? OR reason LIKE ? OR reporter_id LIKE ? OR reported_id LIKE ?)
                            ORDER BY created_at DESC
                            LIMIT ? OFFSET ?
                        ''', (status, search_filter, search_filter, search_filter, search_filter, limit, offset))
                    else:
                        cursor.execute('''
                            SELECT * FROM reports
                            WHERE status = ?
                            ORDER BY created_at DESC
                            LIMIT ? OFFSET ?
                        ''', (status, limit, offset))

                reports = [dict(row) for row in cursor.fetchall()]

                return {
                    "reports": reports,
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "total_pages": (total + limit - 1) // limit if total > 0 else 1
                }
        except Exception as e:
            logger.error(f"Ошибка get_reports_by_status_paginated: {e}")
            return {"reports": [], "total": 0, "page": page, "limit": limit, "total_pages": 1}
