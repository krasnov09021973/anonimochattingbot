# handlers/rating.py
"""Обработчики оценок (callback)"""

from aiogram import Router
from aiogram.types import CallbackQuery

rating_router = Router()


@rating_router.callback_query(lambda c: c.data.startswith('rate:'))
async def process_rating(callback: CallbackQuery):
    """Обработка оценки собеседника"""
    await callback.answer(get_message('rate_good'), show_alert=False)
    await callback.message.delete()
