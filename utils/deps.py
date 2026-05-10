# utils/deps.py
"""
Глобальные зависимости бота.
Устанавливаются в main.py при запуске.
"""

_universe = None
_user_repo = None
_chat_repo = None
_report_repo = None
_ai_repo = None
_bot = None

def set_bot(value):
    global _bot
    _bot = value

def get_bot():
    return _bot

def set_universe(value):
    global _universe
    _universe = value


def get_universe():
    return _universe


def set_user_repo(value):
    global _user_repo
    _user_repo = value


def get_user_repo():
    return _user_repo


def set_chat_repo(value):
    global _chat_repo
    _chat_repo = value


def get_chat_repo():
    return _chat_repo


def set_report_repo(value):
    global _report_repo
    _report_repo = value


def get_report_repo():
    return _report_repo


def set_ai_repo(value):
    global _ai_repo
    _ai_repo = value


def get_ai_repo():
    return _ai_repo
