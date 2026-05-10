# handlers/__init__.py
"""
Пакет обработчиков сообщений Telegram.

Каждый файл содержит一组 обработчиков для определенных команд или типов сообщений.
Все роутеры импортируются в main.py и регистрируются в диспетчере.
"""

from .start import router as start
from .search import router as search
from .chat import router as chat
from .rating import router as rating
from .report import router as report
from .admin import router as admin

