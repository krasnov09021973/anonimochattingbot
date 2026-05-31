# handlers/lang.py
from aiogram import Router
from aiogram.types import CallbackQuery
from lang import get_message, get_available_languages

router = Router()

@router.callback_query(lambda c: c.data.startswith('lang:'))
async def change_language(callback: CallbackQuery, user_repo):
    user_id = callback.from_user.id
    new_lang = callback.data.split(':')[1]

    # Сохраняем язык в БД
    await user_repo.set_user_lang(user_id, new_lang)

    # Получаем название языка на новом языке
    languages = get_available_languages()
    lang_name = languages.get(new_lang, {}).get('name', new_lang)

    await callback.answer()
    await callback.message.edit_text(
        get_message('lang_selected', lang=new_lang, lang_name=lang_name),
        reply_markup=None
    )
