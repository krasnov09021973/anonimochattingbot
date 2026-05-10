# handlers/rating.py
from aiogram import Router
from aiogram.types import CallbackQuery
from utils.tasks import schedule_message_deletion, cancel_deletion

router = Router()


@router.callback_query(lambda c: c.data.startswith('rate:'))
async def process_rating(callback: CallbackQuery):
    await callback.answer("✅", show_alert=False)
    try:
        await callback.message.delete()
    except:
        pass

@router.callback_query(lambda c: c.data.startswith('rate:'))
async def process_rating_callback(callback: CallbackQuery):
    # ... парсим callback_data
    _, partner_id_str, rating, chat_token = callback.data.split(':')
    partner_id = int(partner_id_str)

    if partner_id == 0:
        # Сохраняем оценку AI в ai_feedback
        from services.ai_service import AIService
        ai_service = AIService(get_universe(), get_user_repo(), get_ai_repo())
        ai_char = ai_service.get_character_by_user(user_id)  # нужно реализовать

        db.save_ai_feedback(user_id, ai_char, rating=rating)

        await callback.message.answer("✅ Спасибо за оценку!")
        await callback.message.delete()
        return


    if rating == 'good':
        # ... положительная оценка
        await callback.message.delete()
        await callback.message.answer("✅ Спасибо за оценку!")

    elif rating == 'bad':
        # ... отрицательная оценка
        # Редактируем клавиатуру (убираем 👍, оставляем жалобу)
        new_keyboard = InlineKeyboardBuilder()
        new_keyboard.button(text="👎 Отрицательная оценка", callback_data="void")
        new_keyboard.button(text="⚠️ Жалоба", callback_data=f"rate:{partner_id}:report:{chat_token}")
        new_keyboard.adjust(1)

        await callback.message.edit_reply_markup(reply_markup=new_keyboard.as_markup())
        await callback.answer("👎 Отрицательная оценка учтена")

        # Запускаем таймер на удаление через 60 секунд
        await schedule_message_deletion(
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            delay=60,
            key=callback.data
        )

    elif rating == 'report':
        # Отменяем таймер, если был
        cancel_deletion(callback.data)
        # ... показываем клавиатуру выбора причины жалобы
