"""
Модуль с клавиатурами бота (aiogram 3.x)
Все клавиатуры используют Builder API
"""
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from lang import get_message, get_available_languages

def get_search_start_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Генерирует меню перед стартом поиска (например, Найти собеседника, Мой профиль, Темы)"""
    builder = ReplyKeyboardBuilder()

    # Добавляем только две главные кнопки
    builder.button(text=get_message('btn_search', lang))
    builder.button(text=get_message('btn_topics', lang))

    # Размещаем их в один ряд (или друг под другом, если убрать adjust)
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_search_cancel_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Клавиатура во время поиска"""
    builder = ReplyKeyboardBuilder()

    builder.button(text=get_message('btn_cancel', lang))

    return builder.as_markup(resize_keyboard=True)

def get_language_selection_keyboard() -> InlineKeyboardMarkup:
    """
    ДИНАМИЧЕСКАЯ КЛАВИАТУРА:
    Автоматически строит кнопки на основе файлов, найденных в папке lang/
    """
    builder = InlineKeyboardBuilder()

    # Запрашиваем актуальный, гарантированно заполненный список языков
    active_languages = get_available_languages()

    # Перебираем все загруженные языки (ru, en, es и т.д.)
    for lang_code, lang_data in active_languages.items():
        # Собираем текст кнопки, например: "🇷🇺 Русский" или "🇬🇧 English"
        button_text = f"{lang_data['flag']} {lang_data['name']}"

        # Привязываем callback_data, например: "set_lang:ru"
        builder.button(
            text=button_text,
            callback_data=f"set_lang:{lang_code}"
        )

    # Кнопки будут размещаться по 2 в ряд
    builder.adjust(2)
    return builder.as_markup()

def get_topics_keyboard(topics_list: list, lang: str) -> InlineKeyboardMarkup:
    """
    Динамически строит сетку кнопок тем.
    Все тексты и эмодзи прилетают напрямую из БД, сформированные под нужный язык.
    """
    builder = InlineKeyboardBuilder()

    for topic in topics_list:
        # topic['title'] уже содержит "Гейминг" для ru или "Video Games" для en!
        prefix = "✅ " if topic.get('is_selected') else ""
        button_text = f"{prefix}{topic['emoji']} {topic['title']}"

        builder.button(
            text=button_text,
            callback_data=f"toggle_topic:{topic['topic_id']}"
        )

    # Кнопка назад
    builder.button(text=get_message('btn_back', lang), callback_data="back_to_menu")
    builder.adjust(2)
    return builder.as_markup()

def get_chat_end_keyboard(lang: str) -> ReplyKeyboardMarkup:
    """Клавиатура в активном чате"""
    builder = ReplyKeyboardBuilder()
    builder.button(text=get_message('btn_stop', lang))
    builder.button(text=get_message('btn_partner_info', lang))
    builder.button(text=get_message('btn_next', lang))
    # Кнопки будут размещаться по 3 в ряд
    builder.adjust(3)
    return builder.as_markup(resize_keyboard=True)
