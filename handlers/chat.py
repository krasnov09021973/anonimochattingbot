# handlers/chat.py
"""
Обработчики чата: /stop, /next, пересылка сообщений
"""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyParameters, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, MessageReactionUpdated
from aiogram.filters import Command
from aiogram.enums import ParseMode, ContentType
from datetime import datetime
from utils.deps import get_universe, get_user_repo, get_ai_repo, get_chat_repo
from handlers.keyboards import get_search_start_keyboard, get_chat_end_keyboard, remove_keyboard, get_rating_keyboard
from services.ai_service import AIService
from repositories.user_repo import UserRepo
from repositories.ai_repo import AIRepo

logger = logging.getLogger(__name__)

router = Router()

@router.message(Command("stop"))
async def cmd_stop(message: Message):
    user_id = message.from_user.id
    universe = get_universe()
    user_repo = get_user_repo()
    chat_repo = get_chat_repo()

    if not universe.is_in_chat(user_id):
        await message.answer("❌ Вы не в чате")
        return

    partner_id = universe.get_chat_partner(user_id)
    chat_token = universe.get_chat_token(user_id)
    started_at = universe.get_chat_started_at(user_id)

    if not chat_token or not started_at:
        await message.answer("❌ Ошибка: не удалось завершить чат")
        return

    # Вычисляем длительность
    ended_at = datetime.now().isoformat()
    try:
        start_dt = datetime.fromisoformat(started_at)
        end_dt = datetime.fromisoformat(ended_at)
        duration = int((end_dt - start_dt).total_seconds())
    except:
        duration = 0

    # Сохраняем историю
    success = chat_repo.save_chat_history(
        user1_id=user_id,
        user2_id=partner_id,
        started_at=started_at,
        ended_at=ended_at,
        duration_seconds=duration,
        chat_token=chat_token,
        user_left_first=True
    )

    if success:
        # Удаляем из active_chats
        chat_repo.remove_active_chat(user_id, chat_token)
        if partner_id != 0:
            chat_repo.remove_active_chat(partner_id, chat_token)

    # Завершаем чат у текущего пользователя
    universe.end_chat(user_id)

    # Если чат с живым собеседником
    if partner_id and partner_id != 0:
        # Завершаем чат и у собеседника
        universe.end_chat(partner_id)

        # Отправляем собеседнику уведомление с кнопками оценки
        try:
            await message.bot.send_message(
                partner_id,
                "👋 <b>Собеседник покинул чат</b>",
                reply_markup=remove_keyboard()
            )
            await message.bot.send_message(
                partner_id,
                "🎯 <b>Оцените качество общения:</b>",
                reply_markup=get_rating_keyboard(user_id, chat_token)
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления партнёра: {e}")

    elif partner_id == 0:
        # Завершаем AI сессию
        universe.end_ai_session(user_id)

        # Отправляем пользователю сообщение о завершении (без кнопок)
        await message.answer(
            "✅ <b>Чат завершён</b>",
            reply_markup=remove_keyboard()
        )

        # Отправляем сообщение с кнопками оценки (для AI)
        await message.answer(
            "🎯 <b>Оцените качество общения:</b>",
            reply_markup=get_rating_keyboard(0, chat_token)
        )
        return

    # Отправляем текущему пользователю уведомление с кнопками оценки
    await message.answer(
        "✅ <b>Чат завершён</b>",
        reply_markup=remove_keyboard()
    )
    await message.answer(
        "🎯 <b>Оцените качество общения:</b>",
        reply_markup=get_rating_keyboard(partner_id, chat_token)
    )

@router.message(Command("next"))
async def cmd_next(message: Message):
    """Завершить чат и начать новый поиск"""
    await cmd_stop(message)

    # Запускаем новый поиск
    from handlers.search import start_search
    user_id = message.from_user.id
    search_type = 'normal'
    await start_search(message, user_id, search_type)


@router.message(lambda msg: msg.text == "⏹️ Завершить")
async def handle_end_chat(message: Message):
    await cmd_stop(message)


@router.message(lambda msg: msg.text == "⏭️ Следующий")
async def handle_next_chat(message: Message):
    await cmd_next(message)


@router.message(lambda msg: msg.text == "👤 Профиль")
async def handle_profile_in_chat(message: Message):
    """Показать профиль собеседника (заглушка)"""
    await message.answer("👤 Профиль собеседника (в разработке)")

@router.message_reaction()
async def handle_reaction(event: MessageReactionUpdated):
    """
    Обработчик реакций на сообщения (лайки, сердечки и т.д.)
    """
    user_id = event.user.id

    universe = get_universe()

    # Получаем чат
    mapping = universe.get_cloned_message(user_id, event.message_id)
    if not mapping:
        return

    # Пересылаем реакцию партнёру
    try:
        await event.bot.set_message_reaction(
            chat_id=mapping['partner_id'],
            message_id=mapping['cloned_msg_id'],
            reaction=event.new_reaction
        )
    except Exception as e:
        logger.error(f"Ошибка реакции: {e}")

@router.message(F.content_type.in_({
    ContentType.TEXT,
    ContentType.PHOTO,
    ContentType.VIDEO,
    ContentType.VOICE,
    ContentType.STICKER,
    ContentType.ANIMATION,
    ContentType.AUDIO,
    ContentType.DOCUMENT,
    ContentType.VIDEO_NOTE
}))
async def handle_message(message: Message):
    """Обработка всех текстовых сообщений"""
    user_id = message.from_user.id
    universe = get_universe()

    # Проверяем, в чате ли пользователь
    if not universe.is_in_chat(user_id):
        return

    partner_id = universe.get_chat_partner(user_id)

    # Если чат с AI
    if partner_id == 0:
        # Отправляем сообщение в AI
        user_repo = get_user_repo()
        ai_repo = get_ai_repo()
        ai_service = AIService(universe, user_repo, ai_repo)

        reply = await ai_service.send_message(user_id, message.text)

        if reply == "AI_ERROR":
            await message.answer("❌ Ошибка AI. Попробуйте позже.")
        elif reply == "AI_ERROR_LIMIT":
            await message.answer("❌ Лимит сообщений AI исчерпан.")
        else:
            await message.answer(reply)
        return

    # Если чат с живым собеседником
    try:
        # Проверяем, является ли сообщение ответом на другое
        if message.reply_to_message:
            # Отправляем с цитированием (одно сообщение)
            # await message.send_copy(
            #     chat_id=partner_id,
            #     reply_parameters=ReplyParameters(
            #         chat_id=user_id,
            #         message_id=message.reply_to_message.message_id
            #     )
            # )
            cloned_msg = await message.send_copy(
                chat_id=partner_id,
                reply_parameters=ReplyParameters(
                    chat_id=user_id,
                    message_id=message.reply_to_message.message_id
                )
            )

        else:
            # Обычное сообщение — копируем
            # await message.send_copy(chat_id=partner_id)
            cloned_msg = await message.send_copy(chat_id=partner_id)

        universe.add_message_mapping(user_id, message.message_id, partner_id, cloned_msg.message_id)

    except Exception as e:
        logger.error(f"Ошибка пересылки: {e}")
        await message.answer("❌ Не удалось отправить сообщение.")

