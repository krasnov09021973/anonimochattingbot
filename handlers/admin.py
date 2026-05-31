# handlers/admin.py
"""Админ-команды"""

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from config import settings
from lang import get_message, get_error

admin_router = Router()


@admin_router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Вход в админ-панель"""
    user_id = message.from_user.id

    if user_id not in settings.admin_list:
        await message.answer(get_error('permission_denied'))
        return

    # TODO: генерация PIN и ссылка на админку
    await message.answer(
        get_message('admin_pin', admin_url="https://tgbot.local-net.ru:8444", pin="123456")
    )
