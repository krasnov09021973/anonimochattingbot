# handlers/start.py
"""
Обработчики команд /start, /menu, /id и кнопок главного меню
"""

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from handlers.keyboards import get_search_start_keyboard
from utils.deps import get_universe, get_user_repo

router = Router()

@router.message(Command("start", "menu"))
async def cmd_start(message: Message):
    """
    Команда /start или /menu — показывает главный экран бота.

    Здесь пользователь может:
    - Начать поиск собеседника
    - Перейти в свой профиль
    - Выбрать темы
    - Узнать о премиуме и т.д.
    """
    user_id = message.from_user.id

    universe = get_universe()  # ← без аргументов
    user_repo = get_user_repo() # ← без аргументов

    # Если пользователь в чате — сначала он должен его завершить
    if universe.is_in_chat(user_id):
        await message.answer(
            "❌ Вы сейчас в чате!\n\n"
            "Сначала завершите текущий диалог (кнопка '⏹️ Завершить'), "
            "а затем начните поиск снова."
        )
        return

    # Убеждаемся, что пользователь не в поиске
    universe.remove_from_queue(user_id)

    # Регистрируем или обновляем пользователя в БД
    username = message.from_user.username
    user_repo.add_or_update_user(user_id, username)
    user_repo.update_activity(user_id)

    # Приветственное сообщение
    welcome_text = (
        "✨ <b>Добро пожаловать в Анонимный Чат!</b> ✨\n\n"
        "👇 <i>Основные функции:</i>\n"
        "• <b>🔍 Поиск собеседника</b> — найти собеседника\n"
        "• <b>🎯 Мои темы</b> — выбрать темы для общения\n\n"
        "📜 Используя бота, вы принимаете условия "
        "<a href='https://tgbot.local-net.ru:8444/oferta.html'>оферты</a>."
    )

    await message.answer(
        welcome_text,
        reply_markup=get_search_start_keyboard()  # ← используем правильную клавиатуру
    )


@router.message(Command("id", "myid"))
async def cmd_id(message: Message):
    """Команда /id — показывает ID пользователя"""
    user_id = message.from_user.id
    await message.answer(
        f"🆔 <b>Ваш ID:</b> <code>{user_id}</code>\n\n"
        f"📝 <i>Может понадобиться для связи с поддержкой</i>"
    )
