# services/limits_service.py
"""
Сервис для проверки и обновления лимитов.
"""

import logging
import asyncio
import random
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, user_repo, chat_repo, topic_repo, limits_service, ai_service, bot):
        self.user_repo = user_repo
        self.chat_repo = chat_repo
        self.topic_repo = topic_repo
        self.limits_service = limits_service
        self.ai_service = ai_service
        self.bot = bot

        # НАША ОЧЕРЕДЬ В ОЗУ: Список словарей.
        # Структура элемента: {"user_id": 123, "entered_at": timestamp, "lang": "ru"}
        self._search_queue: List[Dict[str, Any]] = []

    async def add_to_queue(self, user_id: int, user_lang: str) -> str:
        """
        МГНОВЕННЫЙ МЕТОД: Валидирует пользователя и заносит его в ОЗУ-очередь.
        Никаких вызовов set_search_status в БД здесь больше НЕТ!
        """
        # 1. Быстрая проверка в памяти: не сидит ли юзер в очереди уже?
        if any(player['user_id'] == user_id for player in self._search_queue):
            return "already_searching"

        # 2. Запрашиваем контекст из БД одним запросом (для проверки бана и чата)
        user_ctx = await self.user_repo.get_user_context(user_id)

        if user_ctx.get('is_banned'):
            return "banned"

        if user_ctx.get('in_chat'):
            return "already_in_chat"

        # 3. Достаем пол и выбранные темы пользователя, чтобы зафиксировать их в ОЗУ
        # Это позволит фоновому потоку сравнивать их мгновенно без повторных запросов к БД!
        user_gender = user_ctx.get('gender', 'unknown')
        user_topics = await self.user_repo.get_user_selected_topics(user_id) # Получаем список ID тем

        # 4. Пишем полную карточку пользователя в оперативную память
        import time
        self._search_queue.append({
            "user_id": user_id,
            "entered_at": time.time(),
            "lang": user_lang,
            "gender": user_gender,
            "topics": user_topics  # Список ID тем, например: [1, 3]
        })

        return "added"


    async def remove_from_queue(self, user_id: int) -> bool:
        """
        ЕДИНСТВЕННЫЙ МЕТОД ОТМЕНЫ: Выбрасывает пользователя из ОЗУ-очереди поиска.
        Вызывается, когда пользователь передумал искать чат и нажал кнопку 'Стоп'.

        Выход: True, если пользователь реально был в очереди и мы его удалили.
               False, если его в очереди не оказалось.
        """
        # 1. Проверяем, сидит ли вообще этот ID в нашем списке в памяти
        is_present = any(u['user_id'] == user_id for u in self._search_queue)

        if not is_present:
            # Если юзера в очереди нет (например, конвейер уже соединил его секунду назад), выходим
            return False

        # 2. Мгновенно пересобираем список в ОЗУ, исключая карточку этого пользователя
        # (Базу данных на запись здесь вообще не трогаем — экономим ресурс диска!)
        self._search_queue = [u for u in self._search_queue if u['user_id'] != user_id]

        return True

    async def process_queue_loop(self):
        """
        ГЛАВНЫЙ КОНВЕЙЕР БОТА: Работает в фоне раз в секунду.
        Сравнивает анкеты в ОЗУ, контролирует время ожидания и подключает ИИ.
        """
        from lang import get_message
        from handlers.keyboards import get_chat_end_keyboard
        import time
        import random

        while True:
            try:
                # Получаем точный размер очереди в памяти
                total_queue_len = len(self._search_queue)

                # Отладочный лог тика, если в очереди кто-то есть
                if total_queue_len > 0:
                    logger.info(f"[CONVEYOR_TICK] Очередь не пуста. Всего человек в ОЗУ: {total_queue_len}")
                else:
                    # Если пуста — спим без лишнего флуда в консоль
                    await asyncio.sleep(1)
                    continue

                # Копируем список очереди на текущий тик
                current_queue = list(self._search_queue)

                for current_user in current_queue:
                    if current_user not in self._search_queue:
                        continue

                    user_id = current_user['user_id']
                    user_lang = current_user['lang']

                    # -------------------------------------------------------------
                    # ЭТАП 1: ИЩЕМ ЖИВОГО СОБЕСЕДНИКА (ПО ПОЛУ И ТОПИКАМ)
                    # -------------------------------------------------------------
                    matched_partner = None
                    common_topic_id = None
                    is_general_search = False

                    for potential_partner in self._search_queue:
                        if potential_partner['user_id'] == user_id:
                            continue

                        gender_a = current_user.get('gender', 'unknown')
                        gender_b = potential_partner.get('gender', 'unknown')

                        if gender_a != 'unknown' and gender_b != 'unknown':
                            if gender_a == gender_b:
                                continue

                        topics_a = current_user.get('topics') or []
                        topics_b = potential_partner.get('topics') or []

                        if topics_a and topics_b:
                            shared_topics = set(topics_a) & set(topics_b)
                            if shared_topics:
                                matched_partner = potential_partner
                                common_topic_id = random.choice(list(shared_topics))
                                is_general_search = False
                                break
                        elif not topics_a or not topics_b:
                            matched_partner = potential_partner
                            common_topic_id = None
                            is_general_search = True
                            break

                    # СТЫКОВКА ЖИВЫХ ЛЮДЕЙ
                    if matched_partner:
                        logger.info(f"[MATCH_FOUND] Найдена живая пара: {user_id} <-> {matched_partner['user_id']}")
                        partner_id = matched_partner['user_id']
                        partner_lang = matched_partner['lang']

                        self._search_queue = [u for u in self._search_queue if u['user_id'] not in (user_id, partner_id)]
                        chat_token = await self.chat_repo.create_active_chat(user1_id=user_id, user2_id=partner_id)

                        if is_general_search or common_topic_id is None:
                            t_emoji = "🎲"
                            raw_t_name = "general_chat"
                        else:
                            topic_info = await self.topic_repo.get_topic_by_id(common_topic_id)
                            t_emoji = topic_info.get('emoji', '🎯')
                            raw_t_name = topic_info.get('name', 'general_chat')

                        from lang import AVAILABLE_LANGUAGES

                        lang_mod_u1 = AVAILABLE_LANGUAGES[user_lang]['module']
                        t_name_u1 = getattr(lang_mod_u1, 'TOPIC_NAMES', {}).get(raw_t_name, raw_t_name)
                        text_u1 = get_message('chat_started', lang=user_lang) if raw_t_name == "general_chat" else get_message('chat_started_with_topic', lang=user_lang, topic_emoji=t_emoji, topic_name=t_name_u1)

                        await self.bot.send_message(chat_id=user_id, text=text_u1, reply_markup=get_chat_end_keyboard(user_lang))

                        lang_mod_u2 = AVAILABLE_LANGUAGES[partner_lang]['module']
                        t_name_u2 = getattr(lang_mod_u2, 'TOPIC_NAMES', {}).get(raw_t_name, raw_t_name)
                        text_u2 = get_message('chat_started', lang=partner_lang) if raw_t_name == "general_chat" else get_message('chat_started_with_topic', lang=partner_lang, topic_emoji=t_emoji, topic_name=t_name_u2)

                        await self.bot.send_message(chat_id=partner_id, text=text_u2, reply_markup=get_chat_end_keyboard(partner_lang))
                        continue

                    # -------------------------------------------------------------
                    # ЭТАП 2: AI ТАЙМАУТ (Адаптивная логика на основе старой check_queue)
                    # -------------------------------------------------------------
                    time_in_queue = time.time() - current_user['entered_at']
                    total_queue_len = len(self._search_queue)

                    # Устанавливаем базовый порог подключения ИИ в зависимости от длины очереди
                    if total_queue_len == 1:
                        # Сценарий А: Пользователь ОДИН в очереди.
                        # ИЗМЕНЕНО: Задаем случайный выбор между 10 и 30 секундами!
                        rng = random.Random(user_id)
                        ai_trigger_time = rng.randint(10, 30)
                    else:
                        # Сценарий Б: В очереди есть люди, но мэтч по темам не сросся.
                        # Даем им больше времени на ожидание живого человека
                        rng = random.Random(user_id)
                        ai_trigger_time = 10 + rng.randint(10, 30)  # Даст от 10 до 30 секунд

                    # ВЫВОДИМ ТЕКУЩИЙ СТАТУС ОЖИДАНИЯ В КОНСОЛЬ КАЖДУЮ СЕКУНДУ
                    logger.info(
                        f"[AI_TIMER] Юзер {user_id} | Ждет в ОЗУ: {int(time_in_queue)} сек. | "
                        f"Порог триггера ИИ: {ai_trigger_time} сек. | Всего в очереди: {total_queue_len}"
                    )

                    if time_in_queue >= ai_trigger_time:
                        # ... проверка форы длины очереди ...

                        logger.info(f"[AI_TRIGGER] Порог времени пройден! Удаляем {user_id} из ОЗУ и запускаем ИИ сессию...")

                        # А. Удаляем заждавшегося пользователя из ОЗУ-очереди поиска
                        self._search_queue = [u for u in self._search_queue if u['user_id'] != user_id]

                        # Б. Запускаем сессию, передавая готовые данные из карточки ОЗУ
                        ai_char = await self.ai_service.start_session(
                            user_id=user_id,
                            user_gender=current_user.get('gender', 'unknown'),
                            user_topics=current_user.get('topics') or [],
                            user_lang=user_lang
                        )

                        # В. Если сессия успешно стартовала и карточка вернулась
                        if ai_char and ai_char.get('id'):
                            # Г. МАСКИРОВКА ИНТЕРФЕЙСА (По латинскому флагу general_chat)
                            if ai_char.get('topic') != "general_chat" and current_user.get('topics'):
                                # Имитируем тематический чат...
                                # (ваш текущий код отправки chat_started_with_topic)
                                pass
                            else:
                                # Имитируем обычный случайный чат
                                await self.bot.send_message(
                                    chat_id=user_id,
                                    text=get_message('chat_started', lang=user_lang),
                                    reply_markup=get_chat_end_keyboard(user_lang)
                                )
                        else:
                            logger.warning(f"[AI_FAIL] Ошибка старта ИИ для {user_id}")
                        continue

            except Exception as e:
                logger.error(f"[QUEUE_CONVEYOR] Критическая ошибка в фоновом цикле: {e}", exc_info=True)

            # Каждую секунду проверяем заново
            await asyncio.sleep(1)
