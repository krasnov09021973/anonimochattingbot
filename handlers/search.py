# handlers/search.py
"""
Обработчики поиска собеседника.
Команды: /search, кнопки поиска, отмена поиска
"""

import logging
from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from handlers.keyboards import (
    get_search_cancel_keyboard,
    get_search_type_keyboard,
    remove_keyboard
)
from utils.deps import get_universe, get_user_repo

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("search"))
async def cmd_search(message: Message):
    """
    Команда /search — начать поиск собеседника.
    """
    user_id = message.from_user.id

    universe = get_universe()  # ← без аргументов
    user_repo = get_user_repo() # ← без аргументов

    # 1. Проверка, не в чате ли
    if universe.is_in_chat(user_id):
        await message.answer(
            "❌ Вы уже в чате!\n\n"
            "Сначала завершите текущий диалог (кнопка '⏹️ Завершить')."
        )
        return

    # 2. Проверка, не в поиске ли уже
    if user_id in universe.search_queue:
        await message.answer(
            "⏳ Вы уже в очереди поиска.\n"
            "Ожидайте собеседника...\n\n"
            "Для отмены нажмите '❌ Отменить поиск'."
        )
        return

    # 3. Проверка дневного лимита
    from services.rating_service import RatingService
    rating_service = RatingService(universe, user_repo, None)
    can_chat, msg, limit, used = rating_service.can_chat_today(user_id)

    if not can_chat:
        await message.answer(msg)
        return

    # 4. Определяем тип поиска (по умолчанию normal)
    search_type = universe.user_states.get(user_id, {}).get('search_type', 'normal')

    # 5. Если премиум или админ — можно выбрать фильтр по полу
    if user_repo.is_premium(user_id) or user_repo.is_admin(user_id):
        # Запрашиваем тип поиска у пользователя
        universe.user_states[user_id] = universe.user_states.get(user_id, {})
        universe.user_states[user_id]['awaiting_search_type'] = True

        await message.answer(
            "🔍 <b>Выберите тип поиска:</b>\n\n"
            "👥 <b>Обычный поиск</b> — все пользователи\n"
            "👩 <b>Только девушки</b>\n"
            "👨 <b>Только парни</b>",
            reply_markup=get_search_type_keyboard()
        )
        return

    # 6. Обычный поиск (без фильтра)
    await start_search(message, user_id, 'normal')


async def start_search(message: Message, user_id: int, search_type: str = 'normal'):
    """
    Запускает поиск собеседника.
    """
    universe = get_universe()  # ← без аргументов
    user_repo = get_user_repo() # ← без аргументов

    # Проверка лимитов
    from services.rating_service import RatingService
    rating_service = RatingService(universe, user_repo, None)
    can_chat, msg, limit, used = rating_service.can_chat_today(user_id)

    if not can_chat:
        await message.answer(msg)
        return

    # Запоминаем тип поиска
    if user_id not in universe.user_states:
        universe.user_states[user_id] = {}
    universe.user_states[user_id]['search_type'] = search_type

    # Увеличиваем счётчик поисков
    user_repo.increment_searches_count(user_id)

    # Добавляем в очередь
    universe.add_to_queue(user_id)

    # Статусное сообщение
    is_premium = user_repo.is_premium(user_id)

    if is_premium:
        status_text = (
            f"🔍 <b>Поиск собеседника...</b>\n\n"
            f"💎 <b>Премиум:</b> безлимит\n"
            f"🎯 <b>Фильтр:</b> "
        )
        if search_type == 'girls_only':
            status_text += "👩 только девушки\n"
        elif search_type == 'boys_only':
            status_text += "👨 только парни\n"
        else:
            status_text += "👥 все\n"
    else:
        remaining = limit - used
        status_text = (
            f"🔍 <b>Поиск собеседника...</b>\n\n"
            f"📊 <b>Чатов на сегодня:</b> {remaining}/{limit}\n"
        )
        if search_type != 'normal':
            status_text += f"🎯 <b>Фильтр:</b> {'👩 девушки' if search_type == 'girls_only' else '👨 парни'}\n"

    status_text += f"👥 <b>В очереди:</b> <code>{len(universe.search_queue)}</code> чел.\n\n"
    status_text += f"<i>Для отмены нажмите кнопку ниже</i>"

    await message.answer(
        status_text,
        reply_markup=get_search_cancel_keyboard()
    )

    logger.info(f"Поиск начат: {user_id} | Тип: {search_type} | Очередь: {len(universe.search_queue)}")


@router.message(lambda msg: msg.text == "🔍 Поиск собеседника")
async def handle_search_button(message: Message):
    """Обработка кнопки '🔍 Поиск собеседника'"""
    await cmd_search(message)


@router.message(lambda msg: msg.text == "❌ Отменить поиск")
async def handle_cancel_search(message: Message):
    """Обработка кнопки '❌ Отменить поиск'"""
    user_id = message.from_user.id
    universe = get_universe()  # ← без аргументов

    if user_id in universe.search_queue:
        universe.remove_from_queue(user_id)
        await message.answer(
            "✅ Поиск остановлен.\n\n"
            "👇 Используйте кнопки ниже для навигации:",
            reply_markup=remove_keyboard()
        )
        # Показываем главное меню
        from handlers.start import cmd_start
        await cmd_start(message)
    else:
        await message.answer("ℹ️ Вы не в поиске.")


@router.message(lambda msg: msg.text in ["👥 Обычный поиск", "👩 Только девушки", "👨 Только парни"])
async def handle_search_type_selection(message: Message):
    """Обработка выбора типа поиска (для премиум-пользователей)"""
    user_id = message.from_user.id
    universe = get_universe()  # ← без аргументов
    user_repo = get_user_repo() # ← без аргументов

    # Проверяем, ожидает ли пользователь выбора типа
    user_state = universe.user_states.get(user_id, {})
    if not user_state.get('awaiting_search_type'):
        return

    # Убираем флаг ожидания
    universe.user_states[user_id]['awaiting_search_type'] = False

    # Определяем тип поиска
    text = message.text
    if text == "👥 Обычный поиск":
        search_type = 'normal'
        await message.answer("✅ Выбран обычный поиск")
    elif text == "👩 Только девушки":
        search_type = 'girls_only'
        await message.answer("✅ Поиск только среди девушек")
    elif text == "👨 Только парни":
        search_type = 'boys_only'
        await message.answer("✅ Поиск только среди парней")
    else:
        await message.answer("❌ Отмена выбора")
        return

    # Запускаем поиск
    await start_search(message, user_id, search_type)
