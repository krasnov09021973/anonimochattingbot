# handlers/report.py
"""Обработчики жалоб (callback)"""

from aiogram import Router
from aiogram.types import CallbackQuery

report_router = Router()


@report_router.callback_query(lambda c: c.data.startswith('report:'))
async def process_report(callback: CallbackQuery):
    """Обработка жалобы"""
    await callback.answer(get_message('report_sent'), show_alert=False)
    await callback.message.delete()
