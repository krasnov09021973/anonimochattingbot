# services/report_service.py
"""
Сервис для обработки жалоб.

Что делает:
1. Создание жалобы
2. Уведомление администраторов
3. Обработка жалобы (подтверждение/отклонение)
4. Автоматические санкции (бан, штраф репутации)
"""

import logging
from typing import Tuple, Optional, Dict, List

from repositories.universe import Universe
from repositories.user_repo import UserRepo
from repositories.chat_repo import ChatRepo
from repositories.report_repo import ReportRepo
from services.rating_service import RatingService

logger = logging.getLogger(__name__)


class ReportService:
    """Сервис для работы с жалобами"""

    def __init__(self, universe: Universe, user_repo: UserRepo,
                 chat_repo: ChatRepo, report_repo: ReportRepo,
                 rating_service: RatingService):
        """
        Инициализация сервиса жалоб.

        :param universe: единое хранилище состояний
        :param user_repo: репозиторий пользователей
        :param chat_repo: репозиторий чатов
        :param report_repo: репозиторий жалоб
        :param rating_service: сервис репутации
        """
        self.universe = universe
        self.user_repo = user_repo
        self.chat_repo = chat_repo
        self.report_repo = report_repo
        self.rating_service = rating_service

    # ================================================================
    # СОЗДАНИЕ ЖАЛОБЫ
    # ================================================================

    async def create_report(self, reporter_id: int, reported_id: int,
                            reason: str, chat_token: str = None) -> Tuple[bool, str, Optional[int]]:
        """
        Создаёт новую жалобу.

        :param reporter_id: ID жалобщика
        :param reported_id: ID нарушителя (0 для AI)
        :param reason: причина жалобы (текст)
        :param chat_token: токен чата (для привязки)
        :return: (успех, сообщение, report_id)
        """
        # 1. Проверка на повторную жалобу в этом чате
        if chat_token and self._already_reported(reporter_id, reported_id, chat_token):
            logger.info(f"Повторная жалоба от {reporter_id} на {reported_id} в чате {chat_token}")
            return False, "❌ Вы уже жаловались на этого собеседника в этом чате", None

        # 2. Проверка на AI
        if reported_id == 0:
            # Жалоба на AI — просто сохраняем в ai_feedback
            logger.info(f"Жалоба на AI от {reporter_id}: {reason}")
            # TODO: сохранить в ai_feedback
            return True, "⚠️ Жалоба принята. Мы учтём её для улучшения AI.", None

        # 3. Проверка на существование пользователя
        reported_user = self.user_repo.get_user(reported_id)
        if not reported_user:
            return False, "❌ Пользователь не найден", None

        # 4. Создаём жалобу в БД
        report_id = self.report_repo.create_report(reporter_id, reported_id, reason, chat_token)

        if report_id <= 0:
            logger.error(f"Ошибка создания жалобы от {reporter_id} на {reported_id}")
            return False, "❌ Ошибка при отправке жалобы", None

        logger.info(f"Создана жалоба #{report_id}: {reporter_id} -> {reported_id}: {reason[:50]}")

        # 5. Уведомляем администраторов
        await self._notify_admins(report_id, reporter_id, reported_id, reason)

        return True, "⚠️ Жалоба отправлена. Модераторы проверят.", report_id

    def _already_reported(self, reporter_id: int, reported_id: int, chat_token: str) -> bool:
        """
        Проверяет, была ли уже жалоба в этом чате.
        """
        reports = self.report_repo.get_reports_by_chat(chat_token)
        for report in reports:
            if report['reporter_id'] == reporter_id and report['reported_id'] == reported_id:
                return True
        return False

    async def _notify_admins(self, report_id: int, reporter_id: int,
                             reported_id: int, reason: str) -> None:
        """
        Отправляет уведомление администраторам о новой жалобе.
        """
        from config import ADMIN_IDS
        from utils.deps import get_bot
        bot = get_bot()

        report_text = (
            f"⚠️ <b>НОВАЯ ЖАЛОБА #{report_id}</b>\n\n"
            f"👤 От: <code>{reporter_id}</code>\n"
            f"👤 На: <code>{reported_id}</code>\n"
            f"📋 Причина: {reason}"
        )

        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(int(admin_id), report_text)
            except Exception as e:
                logger.error(f"Не удалось уведомить админа {admin_id}: {e}")

    # ================================================================
    # ОБРАБОТКА ЖАЛОБ (АДМИНКА)
    # ================================================================

    def get_pending_reports(self, limit: int = 50) -> List[Dict]:
        """Возвращает список непроверенных жалоб"""
        return self.report_repo.get_pending_reports(limit)

    def get_report(self, report_id: int) -> Optional[Dict]:
        """Возвращает информацию о жалобе"""
        return self.report_repo.get_report(report_id)

    async def resolve_report(self, report_id: int, admin_id: int,
                             action: str, notes: str = '') -> Tuple[bool, str]:
        """
        Разрешает жалобу.

        :param report_id: ID жалобы
        :param admin_id: ID администратора
        :param action: 'confirm' (подтвердить) или 'reject' (отклонить)
        :param notes: заметки администратора
        :return: (успех, сообщение)
        """
        # Получаем данные жалобы
        report = self.get_report(report_id)
        if not report:
            return False, "Жалоба не найдена"

        if report['status'] != 'pending':
            return False, f"Жалоба уже обработана (статус: {report['status']})"

        reporter_id = report['reporter_id']
        reported_id = report['reported_id']

        if action == 'confirm':
            # Подтверждаем жалобу — баним нарушителя
            success = self._apply_penalty(reported_id, admin_id, report_id)
            if success:
                self.report_repo.resolve_report(report_id, admin_id, 'confirmed', notes)
                logger.info(f"Жалоба #{report_id} подтверждена администратором {admin_id}")
                return True, f"Пользователь {reported_id} забанен, репутация -10"
            else:
                return False, "Ошибка при применении наказания"

        elif action == 'reject':
            # Отклоняем жалобу — штраф жалобщику за ложную жалобу
            self._penalty_for_false_report(reporter_id, admin_id, report_id)
            self.report_repo.resolve_report(report_id, admin_id, 'rejected', notes)
            logger.info(f"Жалоба #{report_id} отклонена администратором {admin_id}")
            return True, f"Жалоба отклонена. Жалобщику начислен штраф -5 репутации"

        else:
            return False, f"Неизвестное действие: {action}"

    def _apply_penalty(self, user_id: int, admin_id: int, report_id: int) -> bool:
        """
        Применяет наказание к нарушителю (бан и -10 репутации).
        """
        # Блокируем пользователя
        self.user_repo.ban_user(user_id, reason=f"Подтверждённая жалоба #{report_id}")

        # Снимаем 10 репутации
        self.user_repo.change_reputation(user_id, -10, reason=f"Подтверждённая жалоба #{report_id}")

        return True

    def _penalty_for_false_report(self, user_id: int, admin_id: int, report_id: int) -> bool:
        """
        Штраф за ложную жалобу (-5 репутации).
        """
        self.user_repo.change_reputation(user_id, -5, reason=f"Ложная жалоба #{report_id}")
        return True
