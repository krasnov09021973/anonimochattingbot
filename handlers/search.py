"""
Файл: src/handlers/search.py
Компонент: Обработчик интерфейса поиска собеседников.
Полностью динамический: автоматически поддерживает любое количество языков в системе.
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

# Импортируем функции перевода, геттер языков и клавиатуры
from lang import get_message, get_available_languages, get_error
from services.search_service import SearchService
from handlers.keyboards import get_search_cancel_keyboard, get_search_start_keyboard

logger = logging.getLogger(__name__)

# Создаем роутер для поиска собеседников
search_router = Router()


# =====================================================================
# ВСПАМОГАТЕЛЬНАЯ ФУНКЦИЯ (ДИНАМИЧЕСКИЙ ФИЛЬТР КНОПКИ ПОИСКА)
# =====================================================================
def is_search_button(message: Message) -> bool:
    """
    Динамически проверяет, нажал ли пользователь кнопку 'Поиск' на ЛЮБОМ языке.
    Избавляет проект от хардкода конкретных языков (ru, en, es и т.д.) в фильтрах.
    """
    if not message.text:
        return False

    # 1. Запрашиваем актуальный список всех отсканированных языков в системе
    active_languages = get_available_languages()

    # 2. Собираем массив переводов кнопки 'btn_search' для каждого доступного файла
    valid_search_buttons = []
    for lang_code in active_languages.keys():
        translated_text = get_message('btn_search', lang=lang_code)
        valid_search_buttons.append(translated_text)

    # 3. Возвращаем True, если текст сообщения совпал хотя бы с одним из вариантов
    return message.text in valid_search_buttons

def is_cancel_button(message: Message) -> bool:
    """
    Динамически проверяет, нажал ли пользователь кнопку 'Стоп/Выход' на ЛЮБОМ языке.
    Автоматически подтягивает данные из всех файлов в папке lang/.
    """
    if not message.text:
        return False

    # 1. Запрашиваем список всех доступных в системе языков
    active_languages = get_available_languages()

    # 2. Собираем переводы кнопки 'btn_cancel' для каждого языка
    valid_stop_buttons = []
    for lang_code in active_languages.keys():
        translated_text = get_message('btn_cancel', lang=lang_code)
        valid_stop_buttons.append(translated_text)

    # 3. Возвращаем True, если текст пользователя совпал с кнопкой стоп на каком-то языке
    return message.text in valid_stop_buttons

# =====================================================================
# ОСНОВНОЙ ХЭНДЛЕР: ЗАПУСК ПОИСКА СОБЕСЕДНИКА
# =====================================================================
# Триггер А: текстовая команда /search
@search_router.message(Command("search"))
# Триггер Б: клик по динамической кнопке отмены на любом языке
@search_router.message(is_search_button)
async def cmd_search(message: Message, search_service: SearchService, user_lang: str):
    """
    Хэндлер реагирует на команду /search или на клик по физической кнопке поиска.
    Помещает пользователя в фоновый конвейер ОЗУ-очереди.
    """
    logger.info(f"[INFO] cmd_search")

    user_id = message.from_user.id

    logger.info(f"[INFO] user_id: {user_id}, user_lang: {user_lang}")

    # 1. Вызываем метод сервиса, чтобы закинуть ID пользователя в быструю память (ОЗУ)
    #    Передаем туда также текущий язык сессии, чтобы фоновый поток знал, как писать юзеру
    result = await search_service.add_to_queue(user_id, user_lang)

    logger.info(f"[INFO] (search_service.add_to_queue) result : {result}")

    # 2. АНАЛИЗИРУЕМ РЕЗУЛЬТАТ ОТ СЕРВИСА И ОТВЕЧАЕМ НА ЯЗЫКЕ СЕССИИ ЮЗЕРА
    if result == "banned":
        # Пользователь забанен, выводим сообщение об ошибке
        await message.answer(get_error('error_banned', lang=user_lang))

    elif result == "already_in_chat":
        # Пользователь уже общается с кем-то прямо сейчас
        await message.answer(get_error('error_already_in_chat', lang=user_lang))

    elif result == "already_searching":
        # Защита от дурака: пользователь нажал кнопку поиска второй раз, пока сидит в очереди
        await message.answer(get_error('error_already_searching', lang=user_lang))

    elif result == "added":
        # УСПЕХ: Пользователь успешно встал на конвейер фонового потока!
        # Отправляем ему системный текст ожидания (например, "⏳ Ищу собеседника...")
        # И подменяем нижнюю клавиатуру на кнопку "❌ Остановить поиск / диалог"
        await message.answer(
            get_message('search_start', lang=user_lang),
            reply_markup=get_search_cancel_keyboard(user_lang)
        )

# Ловим текстовую команду /cancel ИЛИ клик по динамической кнопке на любом языке
# Триггер А: текстовая команда /cancel
@search_router.message(Command("cancel"))
# Триггер Б: клик по динамической кнопке отмены на любом языке
@search_router.message(is_cancel_button)
async def cmd_cancel(message: Message, search_service: SearchService, user_lang: str):
    """
    Хэндлер останавливает текущую активность пользователя (поиск, чат или ИИ).
    Возвращает пользователя к стартовой клавиатуре "Поиск и Темы".
    """
    user_id = message.from_user.id
    bot = message.bot

    # 1. Вызываем наш сервисный метод отмены
    result = await search_service.remove_from_queue(user_id)

    logger.info(f"[INFO] (search_service.remove_from_queue) result : {result}")

    # 2. РАЗБИРАЕМ ВАРИАНТЫ ОТВЕТОВ НА ОСНОВЕ РЕШЕНИЯ СЕРВИСА
    if result:
        # Пользователь успешно вышел из ОЗУ-очереди
        await message.answer(
            get_message('search_cancel', lang=user_lang), # "❌ Поиск остановлен."
            reply_markup=get_search_start_keyboard(user_lang)     # Возвращаем кнопки "Поиск" и "Темы"
        )

    else:
        # Защита от спама: пользователь нажал Стоп, хотя нигде не состоял
        # Используем get_error, так как это логическое предупреждение!
        await message.answer(
            get_error('error_unknown', lang=user_lang),
            reply_markup=get_search_start_keyboard(user_lang)
        )
