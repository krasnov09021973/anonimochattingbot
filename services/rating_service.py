# services/limits_service.py
"""
Сервис для проверки и обновления лимитов.
"""

import logging
from datetime import datetime
from typing import Tuple

from repositories.user_repo import UserRepo
from repositories.chat_repo import ChatRepo
from config import settings
from lang import get_error

logger = logging.getLogger(__name__)

class RatingService:
    def __init__(self, user_repo: UserRepo, chat_repo: ChatRepo):
        self.user_repo = user_repo
        self.chat_repo = chat_repo

