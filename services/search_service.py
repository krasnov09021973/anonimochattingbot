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
                # Если очередь в оперативной памяти полностью пуста — спать 1 секунду
                if not self._search_queue:
                    await asyncio.sleep(1)
                    continue

                # Копируем список очереди на текущий тик, чтобы избежать ошибок
                # при удалении элементов прямо во время итерации цикла.
                current_queue = list(self._search_queue)
                import time

                for current_user in current_queue:
                    # Защита: если пользователя уже соединили или удалили на этом тике — пропускаем
                    if current_user not in self._search_queue:
                        continue

                    user_id = current_user['user_id']
                    user_lang = current_user['lang']

                    # -------------------------------------------------------------
                    # ЭТАП 1: ИЩЕМ ЖИВОГО СЛУЧАЙНОГО СОБЕСЕДНИКА С СОВПАДАЮЩИМИ ТОПИКАМИ
                    # -------------------------------------------------------------
                    matched_partner = None
                    common_topic_id = None

                    # Ищем пару среди ВСЕХ ОСТАЛЬНЫХ людей, кто сейчас сидит в ОЗУ-списке
                    for potential_partner in self._search_queue:
                        # Не соединяем человека с самим собой!
                        if potential_partner['user_id'] == user_id:
                            continue

                        # Пересекаем списки ID выбранных тем через множества (set)
                        # В add_to_queue мы сохранили списки ID тем в ключе 'topics'
                        shared_topics = set(current_user['topics']) & set(potential_partner['topics'])

                        if shared_topics:
                            # Нашли человека со схожими интересами! Запоминаем его
                            matched_partner = potential_partner
                            # Вытаскиваем ID одной случайной общей темы из совпавших
                            common_topic_id = random.choice(list(shared_topics))
                            break

                    # -------------------------------------------------------------
                    # СТЫКОВКА: ЕСЛИ ЖИВОЙ ПАРТНЕР ПО ИНТЕРЕСАМ УСПЕШНО НАЙДЕН
                    # -------------------------------------------------------------
                    if matched_partner:
                        partner_id = matched_partner['user_id']
                        partner_lang = matched_partner['lang']

                        # А. Мгновенно удаляем ОБОИХ участников из нашей быстрой ОЗУ-очереди
                        self._search_queue = [u for u in self._search_queue if u['user_id'] not in (user_id, partner_id)]

                        # Б. По нашей новой прямой линии создаем запись чата в active_chats
                        # Метод возвращает сгенерированный UUID-токен
                        chat_token = await self.chat_repo.create_active_chat(user1_id=user_id, user2_id=partner_id)

                        # В. Запрашиваем из базы данных emoji и название общей темы по её ID
                        topic_info = await self.topic_repo.get_topic_by_id(common_topic_id)
                        t_emoji = topic_info.get('emoji', '🎯')
                        raw_t_name = topic_info.get('name', 'Общение')

                        # Г. Отправляем красивое тематическое приветствие обоим участникам на их родных языках
                        from lang import AVAILABLE_LANGUAGES

                        # Перевод темы для первого юзера
                        lang_mod_u1 = AVAILABLE_LANGUAGES[user_lang]['module']
                        t_name_u1 = getattr(lang_mod_u1, 'TOPIC_NAMES', {}).get(raw_t_name, raw_t_name)
                        await self.bot.send_message(
                            chat_id=user_id,
                            text=get_message('chat_started_with_topic', lang=user_lang, topic_emoji=t_emoji, topic_name=t_name_u1),
                            reply_markup=get_chat_end_keyboard(user_lang)
                        )

                        # Перевод темы для его партнера
                        lang_mod_u2 = AVAILABLE_LANGUAGES[partner_lang]['module']
                        t_name_u2 = getattr(lang_mod_u2, 'TOPIC_NAMES', {}).get(raw_t_name, raw_t_name)
                        await self.bot.send_message(
                            chat_id=partner_id,
                            text=get_message('chat_started_with_topic', lang=partner_lang, topic_emoji=t_emoji, topic_name=t_name_u2),
                            reply_markup=get_chat_end_keyboard(partner_lang)
                        )
                        continue # Пара создана, переходим к обработке следующего человека

                    # -------------------------------------------------------------
                    # ЭТАП 2: КОНТРОЛЬ ОГРАНИЧЕНИЯ ВРЕМЕНИ ОЖИДАНИЯ (ТАЙМАУТ -> ИИ)
                    # -------------------------------------------------------------
                    time_in_queue = time.time() - current_user['entered_at']

                    # Фиксированный/случайный таймаут маскировки, чтобы скрыть робота
                    ai_trigger_time = random.randint(15, 30)

                    if time_in_queue >= ai_trigger_time:
                        # 1. Сразу удаляем заждавшегося пользователя из ОЗУ-очереди поиска
                        self._search_queue = [u for u in self._search_queue if u['user_id'] != user_id]

                        # 2. ИСПРАВЛЕНО: Вызываем ваш родной асинхронный метод из ai_service!
                        #    Никаких self.ai_repo здесь больше нет. Передаем параметры из ОЗУ
                        ai_char = await self.ai_service.get_random_character(
                            gender_filter="normal",
                            user_topics=current_user['topics'],
                            user_gender=current_user['gender']
                        )

                        # 3. Если персонаж успешно подобрался
                        if ai_char and ai_char.get('id'):
                            # Вызываем метод старта сессии, который мы только что очистили от SQL-запросов!
                            await self.ai_service.start_session(user_id)

                            # 4. МАСКИРОВКА ПОД ОЖИДАНИЯ ЮЗЕРА (Тематический или Обычный чат)
                            if ai_char['topic'] != "обычный чат" and current_user['topics']:
                                # Имитируем, что нашли живого человека по интересам!
                                raw_t_name = ai_char['topic']
                                topic_info = await self.user_repo.get_topic_by_name(raw_t_name)
                                t_emoji = topic_info.get('emoji', '🎯') if topic_info else '🎯'

                                from lang import AVAILABLE_LANGUAGES
                                lang_mod = AVAILABLE_LANGUAGES[user_lang]['module']
                                t_name_u1 = getattr(lang_mod, 'TOPIC_NAMES', {}).get(raw_t_name, raw_t_name)

                                await self.bot.send_message(
                                    chat_id=user_id,
                                    text=get_message('chat_started_with_topic', lang=user_lang, topic_emoji=t_emoji, topic_name=t_name_u1),
                                    reply_markup=get_stop_keyboard(user_lang)
                                )
                            else:
                                # Имитируем обычный чат без тем. Шлем ваш реальный ключ 'chat_started'!
                                await self.bot.send_message(
                                    chat_id=user_id,
                                    text=get_message('chat_started', lang=user_lang),
                                    reply_markup=get_stop_keyboard(user_lang)
                                )
                        continue

            except Exception as e:
                logger.error(f"[QUEUE_CONVEYOR] Критическая ошибка в фоновом цикле: {e}", exc_info=True)

            # Ровно через 1 секунду конвейер проснется и проверит очередь заново
            await asyncio.sleep(1)
