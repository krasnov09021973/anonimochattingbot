"""
Анонимный чат-бот для Telegram
Версия: 4.0.0 (Оптимизированная)
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from lang import scan_languages

# Глобальные импорты (устраняем скрытые зависимости)
from repositories.user_repo import UserRepo
from repositories.chat_repo import ChatRepo
from repositories.ai_repo import AIRepo
from repositories.topic_repo import TopicRepo
from repositories.report_repo import ReportRepo

from services.limits_service import LimitsService
from services.ai_service import AIService
from services.chat_service import ChatService
from services.search_service import SearchService
from services.rating_service import RatingService
from services.report_service import ReportService
from services.user_service import UserService
# В начало main.py добавляем импорт:
from utils.middlewares import ActivityMiddleware, LanguageMiddleware

from handlers import (
    start_router, search_router, chat_router, profile_router,
    rating_router, report_router, admin_router, premium_router
)

# ========== НАСТРОЙКА ЛОГИРОВАНИЯ ==========
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(settings.log_dir / "bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ========== ИНИЦИАЛИЗАЦИЯ ЗАВИСИМОСТЕЙ ==========

def init_repositories() -> tuple:
    """Инициализирует все репозитории (синглтоны для всего приложения)"""
    db = settings.db_path
    return (
        UserRepo(db),
        ChatRepo(db),
        AIRepo(db),
        TopicRepo(db),
        ReportRepo(db)
    )

def init_services(user_repo, chat_repo, ai_repo, topic_repo, report_repo, bot) -> dict:
    """Инициализирует все сервисы"""
    limits_service = LimitsService(user_repo)
    ai_service = AIService(user_repo, ai_repo)

    return {
        'limits_service': limits_service,
        'ai_service': ai_service,
        'chat_service': ChatService(user_repo, chat_repo, limits_service, ai_service),
        'search_service': SearchService(user_repo, chat_repo, topic_repo, limits_service, ai_service, bot),
        'rating_service': RatingService(user_repo, chat_repo),
        'report_service': ReportService(report_repo, user_repo),
        'user_service': UserService(user_repo, topic_repo),
    }

def init_handlers() -> list:
    """Возвращает список зарегистрированных роутеров"""
    return [
        start_router, search_router, chat_router, profile_router,
        rating_router, report_router, admin_router, premium_router,
    ]


# ========== ФОНОВЫЕ ЗАДАЧИ ==========

async def check_queue():
    """Проверка очереди поиска"""
    logger.info("[QUEUE] Фоновая задача заведена в систему")
    # Пока нет реализации, не тратим ресурсы процессора коротким таймером
    while True:
        await asyncio.sleep(60)


async def cleanup_old_chats():
    """Очистка старых неактивных чатов"""
    logger.info("[CLEANUP] Задача очистки чатов запущена")
    while True:
        # TODO: Реализовать логику через chat_service
        await asyncio.sleep(3600)  # Раз в час


async def deactivate_old_users(user_repo: UserRepo):
    """Фоновая задача: раз в сутки деактивировать неактивных пользователей"""
    logger.info("[CLEANUP] Задача деактивации пользователей запущена")
    while True:
        try:
            # Переиспользуем готовый репозиторий, не плодим подключения!
            count = await user_repo.deactivate_inactive_users(days=30)
            if count > 0:
                logger.info(f"[CLEANUP] Деактивировано {count} неактивных пользователей")
        except Exception as e:
            logger.error(f"[CLEANUP] Ошибка деактивации: {e}", exc_info=True)

        await asyncio.sleep(86400)  # Раз в сутки


# ========== LIFESPAN ==========

@asynccontextmanager
async def lifespan(dispatcher: Dispatcher, bot: Bot, user_repo: UserRepo, services: dict):
    """Управление жизненным циклом бота"""
    logger.info("🚀 Бот запускается...")

    # Запускаем фоновые задачи, передавая зависимости
    # Достаем наш инициализированный search_service из общего словаря сервисов
    search_service = services['search_service']

    # ЗАПУСКАЕМ НАШ НАСТОЯЩИЙ ПОТОК ОЧЕРЕДИ (Вместо старого check_queue)
    asyncio.create_task(search_service.process_queue_loop())

    # Остальные фоновые задачи (очистка чатов и т.д.) оставляем ниже
    asyncio.create_task(cleanup_old_chats())
    asyncio.create_task(deactivate_old_users(user_repo))

    yield

    # =====================================================================
    # БЛОК ОСТАНОВКИ (ВЫПОЛНЯЕТСЯ ПРИ Ctrl + C ИЛИ ВЫКЛЮЧЕНИИ СЕРВЕРА)
    # =====================================================================
    logger.info("🛑 Остановка бота...")

    # По прямой трассе достаем chat_service из словаря сервисов!
    chat_service = services['chat_service']

    # Вызываем наш новый чистый метод сервиса
    await chat_service.clear_all_active_chats()

    # Мягко гасим aiogram и закрываем соединение с серверами Telegram
    await dispatcher.emit_shutdown()
    await bot.session.close()
    logger.info("✅ Бот успешно остановлен")


# ========== ТОЧКА ВХОДА ==========

async def main():
    # -------------------------------------------------------------
    # ШАГ 1: ИНИЦИАЛИЗАЦИЯ И ВЕРИФИКАЦИЯ СЛОЯ ДАННЫХ (БАЗА ДАННЫХ)
    # -------------------------------------------------------------
    user_repo, chat_repo, ai_repo, topic_repo, report_repo = init_repositories()

    # 1.2. АВТОМАТИЧЕСКИЙ ВЫЗОВ СОЗДАНИЯ ТАБЛИЦ (Решаем проблему вызова!)
    logger.info("🛠 Проверка и создание таблиц в базе данных...")
    await user_repo._ensure_tables()
    await chat_repo._ensure_tables()
    await ai_repo._ensure_tables()      # В ai_repo метод назывался без подчеркивания
    await topic_repo._ensure_tables()   # Запустит создание тем и их первоначальное наполнение!
    await report_repo._ensure_tables()
    logger.info("✅ Все таблицы базы данных успешно верифицированы")

    # -------------------------------------------------------------
    # ШАГ 2: НАСТРОЙКА AIOGRAM И ИНИЦИАЛИЗАЦИЯ СЕТЕВОГО КЛИЕНТА BOT
    # -------------------------------------------------------------
    # Мы создаем бота ЗДЕСЬ, чтобы переменная "bot" физически существовала в памяти!
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # -------------------------------------------------------------
    # ШАГ 3: ИНИЦИАЛИЗАЦИЯ СЕРВИСОВ (ТЕПЕРЬ БЕЗОПАСНО ПЕРЕДАЕМ BOT)
    # -------------------------------------------------------------
    # Передаем bot шестым аргументом — теперь Python не выдаст NameError!
    services = init_services(user_repo, chat_repo, ai_repo, topic_repo, report_repo, bot)

    # -------------------------------------------------------------
    # ШАГ 4: НАСТРОЙКА ДИСПЕТЧЕРА И РЕГИСТРАЦИЯ ХЭНДЛЕРОВ
    # -------------------------------------------------------------
    dp = Dispatcher()

    # В хэндлеры отдаем ТОЛЬКО сервисы и бота. Репозитории там запрещены!
    dp.workflow_data.update(services)
    dp.workflow_data['bot'] = bot

    # 4. Регистрация интерфейса
    routers = init_handlers()
    for router in routers:
        dp.include_router(router)

    # Сразу после этого подключаем нашу мидлварь на все сообщения:
    dp.message.middleware(ActivityMiddleware())
    dp.message.middleware(LanguageMiddleware())

    # 5. Инфраструктура
    scan_languages()
    logger.info(f"✅ Зарегистрировано {len(routers)} роутеров")

    # Запуск
    async with lifespan(dp, bot, user_repo, services):
        await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен вручную")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
