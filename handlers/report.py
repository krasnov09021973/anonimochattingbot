# handlers/report.py
from aiogram import Router
from aiogram.types import CallbackQuery

router = Router()


@router.callback_query(lambda c: c.data.startswith('report:'))
async def process_report(callback: CallbackQuery):
    await callback.answer("⚠️", show_alert=False)
    try:
        await callback.message.delete()
    except:
        pass
