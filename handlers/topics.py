"""
Файл: src/handlers/topics.py
Компонент: Обработчик меню интересов (тем общения).
Полностью изолирован от поиска и поддерживает динамическое добавление любых языков.
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

# Импортируем геттер языков, функцию перевода и клавиатуры
from lang import get_message, get_available_languages
from services.user_service import UserService
from handlers.keyboards import get_topics_keyboard, get_search_start_keyboard

# Создаем выделенный роутер для тем
topics_router = Router()


# =====================================================================
# ВСПАМОГАТЕЛЬНАЯ ФУНКЦИЯ (ДИНАМИЧЕСКИЙ ФИЛЬТР КНОПКИ)
# =====================================================================
def is_topics_button(message: Message) -> bool:
    """
    Проверяет, нажал ли пользователь кнопку 'Темы' на ЛЮБОМ языке из папки lang/.
    Защищает код от хардкода конкретных языков (ru, en, es и т.д.).
    """
    if not message.text:
        return False

    # 1. Получаем актуальный список всех загруженных языков в боте
    active_languages = get_available_languages()

    # 2. Собираем массив переводов кнопки 'btn_topics' для каждого языка
    valid_buttons = []
    for lang_code in active_languages.keys():
        translated_text = get_message('btn_topics', lang=lang_code)
        valid_buttons.append(translated_text)

    # 3. Возвращаем True, если текст сообщения совпал хотя бы с одним переводом
    return message.text in valid_buttons


# =====================================================================
# ХЭНДЛЕР 1: ПОЛЬЗОВАТЕЛЬ ВХОДИТ В МЕНЮ ТЕМ (Через команду или кнопку)
# =====================================================================
# Вешаем первый триггер: сработает, если пользователь ввел команду /topics вручную
@topics_router.message(Command("topics"))
# Вешаем второй триггер рядом: сработает, если функция-фильтр вернет True (кнопка на любом языке)
@topics_router.message(is_topics_button)
async def cmd_topics(message: Message, user_service: UserService, user_lang: str):
    """
    Открывает инлайн-меню управления интересами.
    Переменная user_lang автоматически прилетает из сессии (через LanguageMiddleware).
    """
    user_id = message.from_user.id

    # 1. Запрашиваем у сервиса сетку тем с отметками (выбрано/не выбрано)
    topics_data = await user_service.get_topics_menu_data(user_id)

    # 2. Генерируем Inline-клавиатуру с галочками, используя ТЕКУЩИЙ язык сессии юзера
    inline_markup = get_topics_keyboard(topics_data, user_lang)

    # 3. Отправляем меню пользователю
    await message.answer(
        get_message('topics_menu_text', lang=user_lang), # "Выберите темы для поиска:"
        reply_markup=inline_markup
    )


# =====================================================================
# ХЭНДЛЕР 2: КЛИК ПО ТЕМЕ (Включение / Выключение галочки)
# =====================================================================
@topics_router.callback_query(F.data.startswith("toggle_topic:"))
async def handle_toggle_topic(callback: CallbackQuery, user_service: UserService, user_lang: str):
    """
    Срабатывает при клике на тему. Изменяет статус в БД и обновляет галочку на кнопке.
    """
    user_id = callback.from_user.id

    # Парсим ID темы из callback_data (строку "toggle_topic:5" превращаем в число 5)
    topic_id = int(callback.data.split(":")[1])

    # Инвертируем статус в базе данных через сервис (метод вернет True, если тема теперь активна)
    is_now_selected = await user_service.toggle_topic(user_id, topic_id)

    # Показываем всплывающее уведомление сверху экрана Телеграм на текущем языке сессии
    alert_key = 'topic_added' if is_now_selected else 'topic_removed'
    await callback.answer(get_message(alert_key, lang=user_lang))

    # Перечитываем базу данных, чтобы получить измененную галочку
    fresh_topics_data = await user_service.get_topics_menu_data(user_id)
    fresh_inline_markup = get_topics_keyboard(fresh_topics_data, user_lang)

    # Обновляем клавиатуру в текущем сообщении без перезагрузки текста
    await callback.message.edit_reply_markup(reply_markup=fresh_inline_markup)


# =====================================================================
# ХЭНДЛЕР 3: НАЖАТИЕ КНОПКИ " НАЗАД"
# =====================================================================
@topics_router.callback_query(F.data == "back_to_menu")
async def handle_back_to_menu(callback: CallbackQuery, user_lang: str):
    """Удаляет меню тем и возвращает пользователя в главное меню бота"""
    # Удаляем сообщение с кнопками тем, чтобы не засорять чат
    await callback.message.delete()

    # Отправляем главное приветствие и прикрепляем стартовую клавиатуру ("Поиск" и "Темы")
    await callback.message.answer(
        get_message('welcome', lang=user_lang),
        reply_markup=get_search_start_keyboard(user_lang)
    )
    # Гасим часики ожидания на кнопке в Telegram
    await callback.answer()
