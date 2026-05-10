# utils/admin_auth.py
"""
Модуль для генерации и проверки PIN-кодов для входа в админ-панель.
"""

import random
import asyncio
import logging

logger = logging.getLogger(__name__)

# Хранилище PIN-кодов: {pin: user_id}
admin_pins = {}


async def clear_pin(pin: str, delay: int = 300):
    """Удаляет PIN через заданное количество секунд (по умолчанию 300 = 5 минут)"""
    await asyncio.sleep(delay)
    if pin in admin_pins:
        del admin_pins[pin]
        logger.info(f"[AUTH] PIN {pin} автоматически удалён")


def generate_pin(user_id: int) -> str:
    """
    Генерирует случайный 6-значный PIN для администратора.

    :param user_id: ID администратора
    :return: сгенерированный PIN
    """
    pin = str(random.randint(100000, 999999))
    admin_pins[pin] = user_id
    asyncio.create_task(clear_pin(pin))
    logger.info(f"[AUTH] Сгенерирован PIN {pin} для user {user_id}")
    return pin


def verify_pin(pin: str) -> int:
    """
    Проверяет PIN и возвращает user_id, если PIN верен.

    :param pin: введённый PIN
    :return: user_id или None
    """
    user_id = admin_pins.get(pin)
    if user_id:
        # Удаляем использованный PIN
        del admin_pins[pin]
        logger.info(f"[AUTH] PIN {pin} успешно использован пользователем {user_id}")
    else:
        logger.warning(f"[AUTH] Неверная попытка ввода PIN: {pin}")
    return user_id
