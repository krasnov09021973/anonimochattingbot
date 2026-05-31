from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message
from services.user_service import UserService

class ActivityMiddleware(BaseMiddleware):
    """Автоматически обновляет время последней активности пользователя"""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Извлекаем UserService, который мы прокинули в main.py
        user_service: UserService = data.get("user_service")

        if user_service and event.from_user:
            user_id = event.from_user.id
            # Запускаем обновление активности в фоне, чтобы не тормозить ответ пользователю
            import asyncio
            asyncio.create_task(user_service.track_activity(user_id))

        # Передаем управление хэндлеру
        return await handler(event, data)

class LanguageMiddleware(BaseMiddleware):
    """Автоматически достает язык пользователя из кэша сервиса и прокидывает в хэндлер"""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_service: UserService = data.get("user_service")

        user_lang = "ru" # Дефолт
        if user_service and event.from_user:
            # Вызываем наш метод с кэшем. Это мгновенно, так как БД не нагружается!
            user_lang = await user_service.get_user_language(event.from_user.id)

        # Магия: записываем язык в data. Теперь он автоматически прилетит аргументом в хэндлер!
        data["user_lang"] = user_lang

        return await handler(event, data)
