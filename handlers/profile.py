# handlers/profile.py
"""Профиль пользователя"""

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

profile_router = Router()


@profile_router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Показать свой профиль"""
    # TODO: реализовать
    await message.answer("👤 Профиль (в разработке)")
