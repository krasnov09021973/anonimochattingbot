# handlers/__init__.py
"""Пакет хендлеров"""

from .start import start_router
from .topics import topics_router
from .search import search_router
from .chat import chat_router
from .profile import profile_router
from .rating import rating_router
from .report import report_router
from .admin import admin_router
from .premium import premium_router

# Добавьте этот блок в конец файла:
__all__ = [
    "start_router",
    "topics_router",
    "search_router",
    "chat_router",
    "profile_router",
    "rating_router",
    "report_router",
    "admin_router",
    "premium_router",
]
