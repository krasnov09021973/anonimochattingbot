# repositories/__init__.py
"""
Пакет репозиториев для работы с БД.
Каждый репозиторий отвечает за свою группу таблиц.
"""

from .base_repo import BaseRepo
from .user_repo import UserRepo
from .chat_repo import ChatRepo
from .report_repo import ReportRepo
from .ai_repo import AIRepo

__all__ = [
    'BaseRepo',
    'UserRepo',
    'ChatRepo',
    'ReportRepo',
    'AIRepo'
]
