# handlers/premium.py
"""Премиум-подписка"""

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from lang import get_message

premium_router = Router()


@premium_router.message(Command("premium"))
async def cmd_premium(message: Message):
    """Информация о премиум-подписке"""
    # TODO: реализовать
    await message.answer(get_message('premium_info'))
