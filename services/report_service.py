# services/limits_service.py
"""
Сервис для проверки и обновления лимитов.
"""

import logging
from datetime import datetime
from typing import Tuple

from repositories.report_repo import ReportRepo
from repositories.user_repo import UserRepo
from config import settings
from lang import get_error

logger = logging.getLogger(__name__)

class ReportService:
    def __init__(self, report_repo: ReportRepo, user_repo: UserRepo):
        self.report_repo = report_repo
        self.user_repo = user_repo
