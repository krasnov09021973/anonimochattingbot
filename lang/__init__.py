# lang/__init__.py
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_LANGUAGE = 'ru'

# Путь к папке с языками
LANG_DIR = Path(__file__).parent

# Список доступных языков (заполняется автоматически)
# Структура: { 'ru': { 'name': '...', 'flag': '...', 'module': <module> } }
AVAILABLE_LANGUAGES: Dict[str, dict] = {}

def scan_languages() -> Dict[str, dict]:
    """
    Сканирует папку lang/ и определяет доступные языки.
    Ищет файлы формата: ru.py, en.py, de.py и т.д.
    """
    global AVAILABLE_LANGUAGES

    LANGUAGE_META = {
        'ru': {'name': 'Русский', 'flag': '🇷🇺', 'code': 'ru'},
        'en': {'name': 'English', 'flag': '🇬🇧', 'code': 'en'},
        'de': {'name': 'Deutsch', 'flag': '🇩🇪', 'code': 'de'},
        'es': {'name': 'Español', 'flag': '🇪🇸', 'code': 'es'},
        'fr': {'name': 'Français', 'flag': '🇫🇷', 'code': 'fr'},
        'it': {'name': 'Italiano', 'flag': '🇮🇹', 'code': 'it'},
        'zh': {'name': '中文', 'flag': '🇨🇳', 'code': 'zh'},
        'ja': {'name': '日本語', 'flag': '🇯🇵', 'code': 'ja'},
    }

    AVAILABLE_LANGUAGES = {}

    # Сканируем файлы в папке lang/
    for file_path in LANG_DIR.glob("*.py"):
        if file_path.name.startswith('__'):
            continue

        lang_code = file_path.stem  # ru, en и т.д.

        try:
            # Динамический импорт словарей из ru.py / en.py
            module = __import__(f'lang.{lang_code}', fromlist=['MESSAGES', 'ERROR_MESSAGES', 'TOPIC_NAMES', 'TOPIC_EMOJIS'])

            # Проверяем наличие обязательного словаря MESSAGES
            if hasattr(module, 'MESSAGES'):
                meta = LANGUAGE_META.get(lang_code, {'name': lang_code, 'flag': '🏳️', 'code': lang_code})
                AVAILABLE_LANGUAGES[lang_code] = {
                    'name': meta['name'],
                    'flag': meta['flag'],
                    'code': lang_code,
                    'module': module
                }
        except ImportError as e:
            logger.error(f"[LANG] Ошибка импорта файла {lang_code}.py: {e}")
            continue

    logger.info(f"[LANG] Успешно загружено языков: {list(AVAILABLE_LANGUAGES.keys())}")
    return AVAILABLE_LANGUAGES


def get_available_languages() -> Dict[str, dict]:
    """Возвращает список доступных языков"""
    if not AVAILABLE_LANGUAGES:
        scan_languages()
    return AVAILABLE_LANGUAGES


def refresh_languages():
    """Обновляет список языков при добавлении нового файла"""
    scan_languages()
    try:
        from handlers.keyboards import refresh_keyboards
        refresh_keyboards()
    except ImportError:
        logger.warning("[LANG] Не удалось обновить клавиатуры при перезагрузке языков")


def get_message(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """
    Возвращает локализованное сообщение по ключу.
    """
    # Если язык не передан или не поддерживается, берем дефолтный (ru)
    if not lang or lang not in AVAILABLE_LANGUAGES:
        lang = DEFAULT_LANGUAGE

    # Если языки еще не сканировались
    if not AVAILABLE_LANGUAGES:
        scan_languages()

    try:
        # Достаем модуль (например, модуль ru.py)
        lang_module = AVAILABLE_LANGUAGES[lang]['module']
        # Ищем ключ в словаре MESSAGES этого модуля. Если нет — ищем в дефолтном (ru)
        text = getattr(lang_module, 'MESSAGES', {}).get(key)

        if text is None and lang != DEFAULT_LANGUAGE:
            default_module = AVAILABLE_LANGUAGES[DEFAULT_LANGUAGE]['module']
            text = getattr(default_module, 'MESSAGES', {}).get(key, key)
        elif text is None:
            text = key

    except Exception:
        text = key

    # Форматируем строку, если переданы аргументы
    if kwargs and isinstance(text, str):
        try:
            return text.format(**kwargs)
        except KeyError as e:
            logger.error(f"[LANG] Ошибка форматирования ключа '{key}': отсутствует аргумент {e}")
    return text


def get_error(key: str, lang: Optional[str] = None, **kwargs) -> str:
    """
    Возвращает локализованное сообщение об ошибке.
    """
    if not lang or lang not in AVAILABLE_LANGUAGES:
        lang = DEFAULT_LANGUAGE

    if not AVAILABLE_LANGUAGES:
        scan_languages()

    try:
        lang_module = AVAILABLE_LANGUAGES[lang]['module']
        # Ищем в ERROR_MESSAGES. Если нет — падаем на MESSAGES, если и там нет — на русский язык
        error_text = getattr(lang_module, 'ERROR_MESSAGES', {}).get(key)

        if error_text is None:
            error_text = getattr(lang_module, 'MESSAGES', {}).get(key)

        if error_text is None and lang != DEFAULT_LANGUAGE:
            default_module = AVAILABLE_LANGUAGES[DEFAULT_LANGUAGE]['module']
            error_text = getattr(default_module, 'ERROR_MESSAGES', {}).get(key, key)
        elif error_text is None:
            error_text = key

    except Exception:
        error_text = key

    if kwargs and isinstance(error_text, str):
        try:
            return error_text.format(**kwargs)
        except KeyError as e:
            logger.error(f"[LANG] Ошибка форматирования ошибки '{key}': {e}")
    return error_text
