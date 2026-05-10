# main.py
"""
Анонимный чат-бот для Telegram
Версия: 4.0.0 (переписанная, чистая архитектура)

Точка входа в приложение.
Здесь происходит:
1. Загрузка конфигурации
2. Создание экземпляра Universe (единого хранилища состояний)
3. Инициализация бота и диспетчера
4. Регистрация всех обработчиков
5. Запуск поллинга
"""

import asyncio
import logging
import random
import sys
from pathlib import Path

# Добавляем корневую папку в путь (для импортов)
sys.path.insert(0, str(Path(__file__).parent))

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, AI_ENABLED, AI_TIMEOUT, LOG_DIR

# ================================================================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ================================================================

# Формат логов: время - уровень - имя_модуля - сообщение
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Настройка корневого логгера
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_DIR / 'bot.log', encoding='utf-8'),  # Пишем в файл
        logging.StreamHandler()  # Выводим в консоль
    ]
)

logger = logging.getLogger(__name__)

# ================================================================
# ИНИЦИАЛИЗАЦИЯ
# ================================================================
from repositories.universe import Universe
from config import DB_PATH
from repositories.user_repo import UserRepo
from repositories.chat_repo import ChatRepo
from repositories.report_repo import ReportRepo
from repositories.ai_repo import AIRepo
import utils.deps as deps

# ИНИЦИАЛИЗАЦИЯ
universe = Universe()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# РЕПОЗИТОРИИ
user_repo = UserRepo(DB_PATH)
chat_repo = ChatRepo(DB_PATH)
report_repo = ReportRepo(DB_PATH)
ai_repo = AIRepo(DB_PATH)

# СОХРАНЯЕМ В DEPS
deps.set_bot(bot)
deps.set_universe(universe)
deps.set_user_repo(user_repo)
deps.set_chat_repo(chat_repo)
deps.set_report_repo(report_repo)
deps.set_ai_repo(ai_repo)

# РЕГИСТРАЦИЯ РОУТЕРОВ (без workflow_data)
from handlers import start, search, chat, rating, report, admin
dp.include_router(start)
dp.include_router(admin)
dp.include_router(search)
dp.include_router(chat)
dp.include_router(rating)
dp.include_router(report)

logger.info("✅ Все обработчики зарегистрированы")

# ================================================================
# ФОНОВЫЕ ЗАДАЧИ (запускаются параллельно с ботом)
# ================================================================

async def check_queue():
    """
    Фоновая задача для обработки очереди поиска.
    Запускается один раз при старте бота и работает бесконечно.

    Что делает:
    1. Если в очереди 2 и более человек — создаёт чат
    2. Если в очереди 1 человек и включён AI — ждёт таймаут и подключает AI
    """
    from services.chat_service import ChatService
    from services.ai_service import AIService

    chat_service = ChatService(universe, bot, user_repo, chat_repo)
    ai_service = AIService(universe, user_repo, ai_repo)

    while True:
        try:
            # Получаем копию очереди (чтобы не менять оригинал во время итерации)
            queue = universe.get_queue_copy()

            # === 1. Поиск пары среди живых пользователей ===
            if len(queue) >= 2:
                user1 = queue[0]
                # Ищем второго с совпадением тем
                for user2 in queue[1:]:
                    if chat_service.match_topics(user1, user2):
                        # Нашли совпадение по темам
                        await chat_service.create_chat(user1, user2)
                        break
                # Небольшая задержка, чтобы не нагружать процессор
                await asyncio.sleep(0.5)

            # === 2. AI таймаут (если в очереди 1 человек) ===
            elif len(queue) == 1 and AI_ENABLED:
                user_id = queue[0]
                timeout = random.randint(AI_TIMEOUT, 29)
                logger.info(f"[AI] Таймаут для {user_id}: {timeout} секунд")

                # Ждём, но каждую секунду проверяем, не появился ли кто-то в очереди
                for _ in range(timeout):
                    await asyncio.sleep(1)
                    if len(universe.search_queue) > 1:
                        # Появился живой собеседник — не подключаем AI
                        break
                else:
                    # Таймаут истёк, всё ещё один — подключаем AI
                    if user_id in universe.search_queue and not universe.is_in_chat(user_id):
                        universe.remove_from_queue(user_id)
                        await ai_service.start_session(user_id)
                        logger.info(f"[AI] Подключён AI-собеседник для {user_id}")

            await asyncio.sleep(1)
        except Exception as e:
            logger.error(f"Ошибка в check_queue: {e}", exc_info=True)
            await asyncio.sleep(5)


# ================================================================
# ЗАПУСК БОТА
# ================================================================

async def on_startup():
    """Выполняется при запуске бота (один раз)"""
    logger.info("🚀 Бот запускается ver: 3.0 (aiogram 3.x)...")

    # Запускаем фоновую задачу обработки очереди
    asyncio.create_task(check_queue())
    logger.info("✅ Фоновая задача check_queue запущена")


async def on_shutdown():
    """Выполняется при остановке бота"""
    logger.info("🛑 Бот останавливается...")
    # Здесь можно добавить сохранение данных, закрытие соединений и т.д.


async def main():
    """Главная функция — точка входа"""
    # Регистрируем обработчики событий запуска и остановки
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Запускаем поллинг (бот начинает опрашивать Telegram на наличие новых сообщений)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


# ================================================================
# ТОЧКА ВХОДА
# ================================================================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен вручную")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
