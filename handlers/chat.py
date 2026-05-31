# handlers/chat.py
"""Обработчики чата"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from lang import get_message, get_error

chat_router = Router()

@chat_router.message(Command("stop"))
@chat_router.message(F.text == "⏹️ Завершить")
async def cmd_stop(message: Message):
    """Завершить чат"""
    # TODO: реализовать через chat_service
    await message.answer(get_message('chat_ended'))


@chat_router.message(Command("next"))
@chat_router.message(F.text == "⏭️ Следующий")
async def cmd_next(message: Message):
    """Завершить чат и начать новый поиск"""
    await cmd_stop(message)
    await cmd_search(message)


@chat_router.message(F.text == "👤 Профиль")
async def cmd_partner_profile(message: Message):
    """Показать профиль собеседника"""
    # TODO: реализовать
    await message.answer("👤 Профиль собеседника (в разработке)")


# @chat_router.message(F.text, ~F.text.startswith('/'))
# async def handle_message(message: Message):
#     """Обработка текстовых сообщений в чате"""
#     # TODO: реализовать через chat_service
#     await message.answer("💬 Сообщение получено (в разработке)")
