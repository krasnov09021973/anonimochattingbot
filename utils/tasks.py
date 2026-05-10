# utils/tasks.py
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Хранилище активных таймеров
_pending_deletions = {}

async def schedule_message_deletion(chat_id: int, message_id: int, delay: int = 60, key: str = None):
    """
    Запускает таймер на удаление сообщения.
    key — уникальный идентификатор (например, callback_data)
    """
    if key:
        _pending_deletions[key] = {'chat_id': chat_id, 'message_id': message_id}

    await asyncio.sleep(delay)

    # Проверяем, не была ли жалоба уже обработана
    if key and key not in _pending_deletions:
        return  # Жалоба обработана, сообщение уже удалено

    try:
        from main import bot
        await bot.delete_message(chat_id, message_id)
        logger.info(f"Удалено сообщение {message_id} в чате {chat_id} по таймауту")
    except Exception as e:
        logger.error(f"Ошибка удаления сообщения {message_id}: {e}")
    finally:
        if key:
            _pending_deletions.pop(key, None)

def cancel_deletion(key: str):
    """Отменяет удаление для указанного ключа (при нажатии жалобы)"""
    _pending_deletions.pop(key, None)
