# handlers/admin_commands.py
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
import logging

from utils.admin_auth import generate_pin

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    from config import ADMIN_IDS

    logger.info(f"[ADMIN] Команда от {message.from_user.id}")

    if str(message.from_user.id) not in ADMIN_IDS:
        await message.answer("⛔ Доступ запрещён")
        return

    pin = generate_pin(message.from_user.id)

    await message.answer(
        f"👑 <b>Вход в админ-панель</b>\n\n"
        f"Перейдите по адресу: <code>https://tgbot.local-net.ru:8444</code>\n\n"
        f"<b>Ваш PIN-код:</b> <code>{pin}</code>\n\n"
        f"<i>Код действителен 5 минут</i>"
    )
