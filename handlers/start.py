"""Обработчики команд /start, /menu, /id"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from lang import get_message
from services.user_service import UserService
from handlers.keyboards import get_search_start_keyboard, get_language_selection_keyboard

# Создаем локальный роутер
start_router = Router()  # Переименовали в start_router для соответствия вашему main.py


@start_router.message(Command("start", "menu"))
async def cmd_start(message: Message, user_service: UserService, user_lang: str):
    user_id = message.from_user.id
    username = message.from_user.username

    # Сервис регистрирует юзера и обновляет его активность
    await user_service.register_or_resume_user(user_id, username)

    # Если язык не выбран, отправляем Inline-кнопки выбора языка
    if user_lang == 'unknown' or not user_lang:
        await message.answer(
            "👋 Пожалуйста, выберите язык интерфейса:\nPlease choose your language:",
            reply_markup=get_language_selection_keyboard()
        )
        return

    # user_lang уже под рукой, берется из кэша оперативки без нагрузки на БД!
    await message.answer(
        get_message('welcome', lang=user_lang),
        reply_markup=get_search_start_keyboard(user_lang)
    )

# 2. Хэндлер обработки нажатия на кнопку языка (Поместили СЮДА!)
@start_router.callback_query(F.data.startswith("set_lang:"))
async def set_language_handler(callback: CallbackQuery, user_service: UserService):
    user_id = callback.from_user.id
    chosen_lang = callback.data.split(":")[1] # Получаем "ru" или "en"

    # Сохраняем язык в БД и ОЗУ-кэш через сервис
    await user_service.set_user_language(user_id, chosen_lang)

    await callback.answer(get_message('lang_changed', lang=chosen_lang))
    await callback.message.delete() # Удаляем сообщение с кнопками выбора языка

    # Отправляем приветствие на новом языке со стартовой клавиатурой поиска
    await callback.message.answer(
        get_message('welcome', lang=chosen_lang),
        reply_markup=get_search_start_keyboard(chosen_lang)
    )

@start_router.message(Command("id", "myid"))
async def cmd_id(message: Message):
    """Показать ID пользователя"""
    user_id = message.from_user.id

    # Больше никаких "await user_service.get_user_language"
    text = get_message('id_info', lang=user_lang, user_id=user_id)
    await message.answer(text)
