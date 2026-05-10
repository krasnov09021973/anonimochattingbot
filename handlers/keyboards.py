"""
Модуль с клавиатурами бота (aiogram 3.x)
Все клавиатуры используют Builder API
"""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# ========== REPLY-КЛАВИАТУРЫ ==========

def get_main_menu():
    """Главное меню"""
    builder = ReplyKeyboardBuilder()
    buttons = [
        "🔍 Поиск собеседника",
        "👤 Мой профиль",
        "🎯 Мои темы",
        "💎 Премиум",
        "📊 Статистика",
        "❓ Помощь"
    ]
    for btn in buttons:
        builder.button(text=btn)
    builder.adjust(2, 2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

def get_search_start_keyboard():
    """Упрощённое меню при старте"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔍 Поиск собеседника")
    builder.button(text="🎯 Мои темы")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_search_cancel_keyboard():
    """Клавиатура во время поиска"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Отменить поиск")
    return builder.as_markup(resize_keyboard=True)

def get_search_type_keyboard():
    """Выбор типа поиска для премиум"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="👥 Обычный поиск")
    builder.button(text="👩 Только девушки")
    builder.button(text="👨 Только парни")
    builder.button(text="❌ Отменить поиск")
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)

def get_chat_end_keyboard():
    """Клавиатура в активном чате"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="⏹️ Завершить")
    builder.button(text="👤 Профиль")
    builder.button(text="⏭️ Следующий")
    builder.adjust(3)
    return builder.as_markup(resize_keyboard=True)

def get_back_to_menu_keyboard():
    """Возврат в меню"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔙 В главное меню")
    return builder.as_markup(resize_keyboard=True)

def get_back_keyboard():
    """Клавиатура с кнопкой 'Назад' для отмены операции"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔙 Назад")
    return builder.as_markup(resize_keyboard=True)

def get_photos_keyboard():
    """Клавиатура для управления фото (Reply кнопки)"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="➕ Добавить фото")
    builder.button(text="🗑 Удалить фото")
    builder.button(text="🔙 В профиль")
    builder.adjust(3)
    return builder.as_markup(resize_keyboard=True)

# ========== INLINE-КЛАВИАТУРЫ ==========

def get_profile_keyboard(is_admin: bool = False):
    """
    Клавиатура для редактирования профиля
    Все callback_data — простые строки (aiogram 3.x)
    """
    builder = InlineKeyboardBuilder()

    # Основные кнопки (2 в ряд)
    builder.button(text="✏️ Имя в чате", callback_data="profile:edit_name")
    builder.button(text="⚧ Пол", callback_data="profile:edit_gender")
    builder.button(text="🎂 Возраст", callback_data="profile:edit_age")

    if is_admin:
        builder.button(text="🔰 Статус", callback_data="profile:edit_status")
    else:
        builder.button(text="🔰 Статус", callback_data="profile:show_status")

    builder.button(text="📸 Фото", callback_data="profile:edit_photos")

    # Кнопка назад
    builder.button(text="🔙 Назад", callback_data="profile:back")
    builder.adjust(2, 2, 2)

    return builder.as_markup()

# def get_photos_keyboard(is_premium: bool = False):
    # """Клавиатура для управления фото в профиле"""
    # builder = InlineKeyboardBuilder()
    #
    # builder.button(text="📸 Основное", callback_data="photo:set_main")
    # builder.button(text="➕ Добавить", callback_data="photo:add")
    # builder.button(text="🗑 Удалить", callback_data="photo:delete")
    # builder.button(text="🔙 Назад", callback_data="photo:back")
    #
    # builder.adjust(2,2)
    #
    # return builder.as_markup()

def get_gender_keyboard():
    """Выбор пола"""
    builder = InlineKeyboardBuilder()
    builder.button(text="👨 Мужской", callback_data="gender:male")
    builder.button(text="👩 Женский", callback_data="gender:female")
    builder.button(text="🚫 Не указывать", callback_data="gender:unknown")
    builder.button(text="🔙 Назад", callback_data="gender:back")
    builder.adjust(2, 2)
    return builder.as_markup()

def get_age_keyboard():
    """Клавиатура для возраста"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🚫 Скрыть возраст", callback_data="age:hide")
    builder.button(text="🔙 Назад", callback_data="age:back")
    builder.adjust(2)
    return builder.as_markup()

def get_topics_keyboard(user_topics=None):
    """
    Клавиатура выбора интересов
    user_topics: список выбранных тем
    """
    from database import db

    if user_topics is None:
        user_topics_ids = []
    else:
        user_topics_ids = [t['topic_id'] for t in user_topics]

    available = db.get_available_topics()
    builder = InlineKeyboardBuilder()

    # Кнопки интересов
    for topic in available:
        topic_id = topic['topic_id']
        is_selected = topic_id in user_topics_ids
        check = "✅ " if is_selected else "⠀ "
        text = f"{check}{topic['emoji']} {topic['name']}"
        callback = f"topic:toggle:{topic_id}"
        builder.button(text=text, callback_data=callback)

    builder.adjust(2)  # Две в ряд

    # Кнопки управления
    control = InlineKeyboardBuilder()
    control.button(text="🗑️ Сбросить", callback_data="topic:clear_all:0")
    control.button(text="🔙 Назад", callback_data="topic:back:0")
    control.adjust(2)

    builder.attach(control)

    # # Информация о выбранных
    # info = InlineKeyboardBuilder()
    # info.button(text=f"🎯 Выбрано: {len(user_topics_ids)}/10", callback_data="topic:info:0")
    # builder.attach(info)

    return builder.as_markup()

def get_rating_keyboard(partner_id: int, chat_token: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👍", callback_data=f"rate:{partner_id}:good:{chat_token}")
    builder.button(text="👎", callback_data=f"rate:{partner_id}:bad:{chat_token}")
    builder.button(text="⚠️ Жалоба", callback_data=f"rate:{partner_id}:report:{chat_token}")
    builder.adjust(3)
    return builder.as_markup()

def get_premium_keyboard():
    """Премиум-подписка"""
    builder = InlineKeyboardBuilder()
    builder.button(text="7 дней за 100 ⭐ / 199₽", callback_data="premium:buy:7")
    builder.button(text="1 месяц за 250 ⭐ / 499₽", callback_data="premium:buy:30")
    builder.button(text="6 месяцев за 750 ⭐ / 1499₽", callback_data="premium:buy:180")
    builder.button(text="1 год за 1000 ⭐ / 1899₽", callback_data="premium:features:365")
    builder.adjust(2)
    return builder.as_markup()

# def get_report_keyboard(partner_id: int):
#     """Клавиатура для выбора причины жалобы"""
#     builder = InlineKeyboardBuilder()
#     builder.button(text="🚫 Оскорбления", callback_data=f"report:{partner_id}:abuse")
#     builder.button(text="🔞 18+ / Пошлость", callback_data=f"report:{partner_id}:adult")
#     builder.button(text="💼 Реклама/спам", callback_data=f"report:{partner_id}:spam")
#     builder.button(text="🎭 Мошенничество", callback_data=f"report:{partner_id}:scam")
#     builder.button(text="🗣️ Разжигание ненависти", callback_data=f"report:{partner_id}:hate")
#     builder.button(text="📵 Личные данные", callback_data=f"report:{partner_id}:data")
#
#     # Кнопка несовпадения пола (если данные переданы)
#     if partner_gender and user_gender:
#         if user_gender == "female" and partner_gender != "female":
#             builder.button(text="👨 Не парень", callback_data=f"report:{partner_id}:wrong_gender")
#         elif user_gender == "male" and partner_gender != "male":
#             builder.button(text="👩 Не девушка", callback_data=f"report:{partner_id}:wrong_gender")
#
#     builder.button(text="✏️ Другое...", callback_data=f"report:{partner_id}:custom")
#     builder.adjust(2)
#     return builder.as_markup()

def get_report_keyboard(partner_id, partner_gender=None):
    """Клавиатура для выбора причины жалобы"""
    builder = InlineKeyboardBuilder()
    builder.button(text="🚫 Оскорбления", callback_data=f"report:{partner_id}:abuse")
    builder.button(text="🔞 18+ / Пошлость", callback_data=f"report:{partner_id}:adult")
    builder.button(text="💼 Реклама/спам", callback_data=f"report:{partner_id}:spam")
    builder.button(text="🎭 Мошенничество", callback_data=f"report:{partner_id}:scam")
    builder.button(text="🗣️ Разжигание ненависти", callback_data=f"report:{partner_id}:hate")
    builder.button(text="📵 Личные данные", callback_data=f"report:{partner_id}:data")

    # Кнопка несовпадения пола
    if partner_gender == "male":
        builder.button(text="👨 Не парень", callback_data=f"report:{partner_id}:wrong_gender")
    elif partner_gender == "female":
        builder.button(text="👩 Не девушка", callback_data=f"report:{partner_id}:wrong_gender")

    else:
        builder.button(text="👨 Не парень", callback_data=f"report:{partner_id}:fake_male")
        builder.button(text="👩 Не девушка", callback_data=f"report:{partner_id}:fake_female")

    builder.button(text="✏️ Своя причина", callback_data=f"report:{partner_id}:custom")
    builder.adjust(2)
    return builder.as_markup()

def get_admin_keyboard():
    """Админ-панель"""
    builder = InlineKeyboardBuilder()
    buttons = [
        ("📊 Статистика", "admin:stats"),
        ("👥 Пользователи", "admin:users"),
        ("⚠️ Жалобы", "admin:reports"),
        ("💬 Рассылка", "admin:broadcast"),
        ("⚙️ Настройки", "admin:settings"),
        ("🔄 Обновить", "admin:refresh")
    ]
    for text, cb in buttons:
        builder.button(text=text, callback_data=cb)
    builder.adjust(2, 2, 2)
    return builder.as_markup()

def remove_keyboard():
    """Убрать клавиатуру"""
    return ReplyKeyboardRemove()
