# universe.py
"""
Единый центр управления состоянием бота.

ВСЯ динамическая информация (кто с кем в чате, кто в очереди, AI сессии)
хранится здесь. Никаких глобальных переменных в других файлах!

Принцип работы:
1. Бот запускается → создаётся ОДИН экземпляр класса Universe
2. Все обработчики используют этот экземпляр
3. Никакой информации в других местах не хранится
"""

from datetime import datetime
from typing import Dict, Optional, Any, List
import random
import hashlib


class Universe:
    """
    Вселенная бота — единое хранилище всех динамических состояний.

    Что здесь хранится:
    - active_chats: кто с кем в чате (включая AI)
    - ai_sessions: история и персонажи AI
    - search_queue: очередь поиска собеседника
    - user_states: текущее состояние каждого пользователя (idle/searching/chatting)
    - temp_states: временные состояния (ожидание ввода имени, возраста, жалобы)
    """

    def __init__(self):
        # ========== 1. АКТИВНЫЕ ЧАТЫ ==========
        # Структура: { user_id: {'partner': int, 'chat_token': str, 'started_at': str} }
        # user_id - Telegram ID пользователя (ключ)
        # partner - с кем общается (user_id или 0 для AI)
        # chat_token - уникальный идентификатор чата (16 символов)
        # started_at - время начала чата (ISO формат)
        self.active_chats: Dict[int, dict] = {}

        # ========== 2. AI СЕССИИ ==========
        # Структура: { user_id: {'character': dict, 'history': list, 'messages_count': int} }
        # user_id - Telegram ID пользователя
        # character - персонаж AI (имя, возраст, пол, промпт)
        # history - история диалога (список сообщений для OpenRouter)
        # messages_count - количество сообщений в сессии (для лимитов)
        self.ai_sessions: Dict[int, dict] = {}

        # ========== 3. ОЧЕРЕДЬ ПОИСКА ==========
        # Простой список user_id в порядке добавления
        # Кто раньше встал — тот раньше получит собеседника
        self.search_queue: List[int] = []

        # ========== 4. СОСТОЯНИЯ ПОЛЬЗОВАТЕЛЕЙ ==========
        # Структура: { user_id: {'state': str, 'last_chat_token': str, ...} }
        # state: 'idle' - нигде, 'searching' - в поиске, 'chatting' - в чате
        # last_chat_token - токен последнего чата (нужен для жалоб после завершения)
        self.user_states: Dict[int, dict] = {}

        # ========== 5. ВРЕМЕННЫЕ СОСТОЯНИЯ (для ввода данных) ==========
        # Сюда складываем отметки о том, что пользователь ожидает ввода
        self.temp_states: Dict[str, Any] = {
            # Множество user_id, которые сейчас вводят имя в профиле
            'awaiting_name': set(),

            # Множество user_id, которые сейчас вводят возраст
            'awaiting_age': set(),

            # Словарь user_id -> {'partner': int, 'chat_token': str}
            # Пользователь выбрал "Свою причину" в жалобе и ожидает ввода текста
            'custom_complaint': {},
        }

        # ========== 6. МАППИНГ (маппинг message_id в чате ) =============
        # База данных message_id в чате, для возможной пересылки сообщений или установки реакций
        self.message_mapping = {}  # {key: {'partner_id': int, 'cloned_msg_id': int}}

    # ================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ================================================================

    @staticmethod
    def generate_chat_token(user1_id: int, user2_id: int) -> str:
        """
        Генерирует уникальный токен чата.

        Токен нужен, чтобы:
        - Связать жалобу с конкретным чатом
        - Связать оценку с конкретным чатом
        - Искать чат в истории

        Как генерируется:
        Берём ID двух участников + текущее время + случайное число
        Всё склеиваем и пропускаем через MD5.

        Результат: 16-символьная строка (например: 'a6344126c62d12bb')
        """
        # Берём текущее время с микросекундами (чтобы избежать коллизий)
        timestamp = datetime.now().timestamp()
        # Добавляем случайное число для надёжности
        random_salt = random.randint(1000, 9999)
        # Формируем строку
        data = f"{user1_id}:{user2_id}:{timestamp}:{random_salt}"
        # Превращаем в MD5 и берём первые 16 символов
        return hashlib.md5(data.encode()).hexdigest()[:16]

    # ================================================================
    # РАБОТА С ЧАТАМИ
    # ================================================================

    def create_chat(self, user1_id: int, user2_id: int) -> str:
        """
        Создаёт чат между двумя живыми пользователями.

        Что делает:
        1. Генерирует уникальный токен чата
        2. Записывает в active_chats обоих участников
        3. Удаляет обоих из очереди поиска (если были)

        Возвращает chat_token (нужен для сохранения в БД и для жалоб)
        """
        # Генерируем уникальный токен для этого чата
        chat_token = self.generate_chat_token(user1_id, user2_id)
        # Фиксируем время начала чата
        started_at = datetime.now().isoformat()

        # Информация о чате для каждого участника
        chat_info = {
            'partner': user2_id,     # для user1 партнёр — user2
            'chat_token': chat_token,
            'started_at': started_at
        }
        self.active_chats[user1_id] = chat_info

        chat_info = {
            'partner': user1_id,     # для user2 партнёр — user1
            'chat_token': chat_token,
            'started_at': started_at
        }
        self.active_chats[user2_id] = chat_info

        # Убираем обоих из очереди поиска
        self.remove_from_queue(user1_id)
        self.remove_from_queue(user2_id)

        # Обновляем состояния
        self.set_user_state(user1_id, 'chatting')
        self.set_user_state(user2_id, 'chatting')

        return chat_token

    def end_chat(self, user_id: int) -> None:
        """
        Завершает чат для пользователя.

        Важно: перед удалением сохраняет last_chat_token в user_states.
        Это нужно, чтобы после завершения чата пользователь мог:
        - Отправить жалобу (жалоба привязывается к chat_token)
        - Поставить оценку
        """
        if user_id not in self.active_chats:
            return  # Пользователь не в чате — ничего не делаем

        # Сохраняем токен чата перед удалением (пригодится для жалоб)
        chat_token = self.active_chats[user_id].get('chat_token')
        # Инициализируем запись пользователя, если её ещё нет
        if user_id not in self.user_states:
            self.user_states[user_id] = {}
        self.user_states[user_id]['last_chat_token'] = chat_token

        # Удаляем из активных чатов
        del self.active_chats[user_id]

        # Если пользователь был в чате с AI — чистим AI сессию
        self.end_ai_session(user_id)

        # Сбрасываем состояние на 'idle'
        self.set_user_state(user_id, 'idle')

    def get_chat_partner(self, user_id: int) -> Optional[int]:
        """
        Возвращает партнёра пользователя по чату.

        Возвращает:
        - user_id другого пользователя (если чат с живым)
        - 0 (если чат с AI)
        - None (если пользователь не в чате)
        """
        chat_data = self.active_chats.get(user_id)
        if chat_data is None:
            return None
        return chat_data.get('partner')

    def get_chat_token(self, user_id: int) -> Optional[str]:
        """
        Возвращает токен чата для пользователя.

        Токен нужен для:
        - Привязки жалобы к конкретному чату
        - Привязки оценки к конкретному чату
        - Сохранения истории в БД
        """
        chat_data = self.active_chats.get(user_id)
        if chat_data is None:
            return None
        return chat_data.get('chat_token')

    def get_chat_started_at(self, user_id: int) -> Optional[str]:
        """Возвращает время начала чата (ISO формат)"""
        chat_data = self.active_chats.get(user_id)
        if chat_data is None:
            return None
        return chat_data.get('started_at')

    def is_in_chat(self, user_id: int) -> bool:
        """Проверяет, находится ли пользователь в чате (с кем-либо, включая AI)"""
        return user_id in self.active_chats

    def is_chatting_with_ai(self, user_id: int) -> bool:
        """Проверяет, общается ли пользователь с AI"""
        return self.get_chat_partner(user_id) == 0

    # ================================================================
    # РАБОТА С МАППИНГОМ СООБЩЕНИЙ В ЧАТЕ
    # ================================================================

    def add_message_mapping(self, user_id: int, original_msg_id: int, partner_id: int, cloned_msg_id: int):
        key = f"{user_id}:{original_msg_id}"
        self.message_mapping[key] = {
            'partner_id': partner_id,
            'cloned_msg_id': cloned_msg_id
        }

    def get_cloned_message(self, user_id: int, original_msg_id: int):
        key = f"{user_id}:{original_msg_id}"
        return self.message_mapping.get(key)

    def clear_chat_mappings(self, user_id: int, partner_id: int):
        """Удаляет все маппинги для чата"""
        keys_to_delete = []
        for key, value in self.message_mapping.items():
            if value['partner_id'] == partner_id or key.startswith(f"{user_id}:"):
                keys_to_delete.append(key)
        for key in keys_to_delete:
            del self.message_mapping[key]

    # ================================================================
    # РАБОТА С ОЧЕРЕДЬЮ ПОИСКА
    # ================================================================

    def add_to_queue(self, user_id: int) -> None:
        """
        Добавляет пользователя в очередь поиска.

        Проверки:
        - Если уже в очереди — не добавляем повторно
        - Если уже в чате — не добавляем
        """
        # Нельзя добавить в очередь, если уже в чате
        if self.is_in_chat(user_id):
            return
        # Нельзя добавить повторно
        if user_id in self.search_queue:
            return
        self.search_queue.append(user_id)
        # Обновляем состояние
        self.set_user_state(user_id, 'searching')

    def remove_from_queue(self, user_id: int) -> None:
        """Удаляет пользователя из очереди поиска"""
        if user_id in self.search_queue:
            self.search_queue.remove(user_id)
        # Состояние обновим только если не в чате
        if not self.is_in_chat(user_id):
            self.set_user_state(user_id, 'idle')

    def get_queue_size(self) -> int:
        """Возвращает количество человек в очереди"""
        return len(self.search_queue)

    def get_queue_copy(self) -> List[int]:
        """Возвращает копию очереди (для безопасного перебора)"""
        return self.search_queue.copy()

    def pop_next_from_queue(self) -> Optional[int]:
        """
        Извлекает первого пользователя из очереди.
        Возвращает user_id или None, если очередь пуста.
        """
        if not self.search_queue:
            return None
        return self.search_queue.pop(0)

    def get_queue_position(self, user_id: int) -> Optional[int]:
        """Возвращает позицию пользователя в очереди (начиная с 0). None если не в очереди."""
        try:
            return self.search_queue.index(user_id)
        except ValueError:
            return None

    # ================================================================
    # РАБОТА С AI
    # ================================================================

    def start_ai_session(self, user_id: int, character: dict) -> None:
        """
        Начинает AI сессию для пользователя.

        AI считается особым собеседником с partner = 0.
        Сессия хранит:
        - character: данные персонажа (имя, возраст, пол, промпт)
        - history: история диалога (для API OpenRouter)
        - messages_count: счётчик сообщений (для лимитов)
        """
        # Добавляем в активные чаты как чат с AI (partner = 0)
        self.active_chats[user_id] = {
            'partner': 0,                # 0 — код AI
            'chat_token': None,          # У AI нет токена (история не сохраняется)
            'started_at': datetime.now().isoformat()
        }

        # Создаём AI сессию
        self.ai_sessions[user_id] = {
            'character': character,
            'history': [{'role': 'system', 'content': character['prompt']}],
            'messages_count': 0
        }

        # Обновляем состояние пользователя
        self.set_user_state(user_id, 'chatting')

    def end_ai_session(self, user_id: int) -> None:
        """Завершает AI сессию для пользователя (чистит данные)"""
        # Удаляем сессию, если она есть
        self.ai_sessions.pop(user_id, None)
        # Не удаляем из active_chats здесь — это делает end_chat()

    def get_ai_character(self, user_id: int) -> Optional[dict]:
        """
        Возвращает данные персонажа AI для пользователя.
        Возвращает None, если у пользователя нет активной AI сессии.
        """
        session = self.ai_sessions.get(user_id)
        if session is None:
            return None
        return session.get('character')

    def get_ai_history(self, user_id: int) -> Optional[list]:
        """Возвращает историю диалога с AI для пользователя"""
        session = self.ai_sessions.get(user_id)
        if session is None:
            return None
        return session.get('history', [])

    def get_ai_messages_count(self, user_id: int) -> int:
        """Возвращает количество сообщений в AI сессии"""
        session = self.ai_sessions.get(user_id)
        if session is None:
            return 0
        return session.get('messages_count', 0)

    def increment_ai_messages_count(self, user_id: int) -> None:
        """Увеличивает счётчик сообщений в AI сессии"""
        session = self.ai_sessions.get(user_id)
        if session:
            session['messages_count'] = session.get('messages_count', 0) + 1

    def add_ai_message(self, user_id: int, role: str, content: str) -> None:
        """
        Добавляет сообщение в историю AI диалога.

        role: 'user' (сообщение от пользователя) или 'assistant' (ответ AI)
        content: текст сообщения
        """
        session = self.ai_sessions.get(user_id)
        if session is None:
            return
        session['history'].append({'role': role, 'content': content})

    def truncate_ai_history(self, user_id: int, max_messages: int = 21) -> None:
        """
        Обрезает историю AI диалога, оставляя не более max_messages сообщений.
        Первое сообщение (system prompt) всегда сохраняется.
        """
        session = self.ai_sessions.get(user_id)
        if session is None:
            return

        history = session['history']
        if len(history) > max_messages:
            # Сохраняем system prompt (первое сообщение) + последние max_messages-1 сообщений
            session['history'] = [history[0]] + history[-(max_messages - 1):]

    # ================================================================
    # РАБОТА С СОСТОЯНИЯМИ ПОЛЬЗОВАТЕЛЕЙ
    # ================================================================

    def set_user_state(self, user_id: int, state: str) -> None:
        """
        Устанавливает состояние пользователя.

        Допустимые состояния:
        - 'idle':   пользователь нигде (можно начать поиск)
        - 'searching':  в очереди поиска
        - 'chatting':   в чате (с живым или AI)
        """
        if user_id not in self.user_states:
            self.user_states[user_id] = {}
        self.user_states[user_id]['state'] = state

    def get_user_state(self, user_id: int) -> str:
        """Возвращает состояние пользователя. Если записи нет — 'idle'."""
        return self.user_states.get(user_id, {}).get('state', 'idle')

    def is_user_idle(self, user_id: int) -> bool:
        """Проверяет, свободен ли пользователь (не в поиске и не в чате)"""
        return self.get_user_state(user_id) == 'idle'

    def get_last_chat_token(self, user_id: int) -> Optional[str]:
        """Возвращает токен последнего чата пользователя (для жалоб после завершения)"""
        return self.user_states.get(user_id, {}).get('last_chat_token')

    # ================================================================
    # РАБОТА С ВРЕМЕННЫМИ СОСТОЯНИЯМИ (ввод данных)
    # ================================================================

    # ----- Ожидание ввода имени -----
    def set_awaiting_name(self, user_id: int) -> None:
        """Помечает, что пользователь ожидает ввод имени (в профиле)"""
        self.temp_states['awaiting_name'].add(user_id)

    def is_awaiting_name(self, user_id: int) -> bool:
        """Проверяет, ожидает ли пользователь ввод имени"""
        return user_id in self.temp_states['awaiting_name']

    def clear_awaiting_name(self, user_id: int) -> None:
        """Снимает отметку ожидания ввода имени"""
        self.temp_states['awaiting_name'].discard(user_id)

    # ----- Ожидание ввода возраста -----
    def set_awaiting_age(self, user_id: int) -> None:
        """Помечает, что пользователь ожидает ввод возраста"""
        self.temp_states['awaiting_age'].add(user_id)

    def is_awaiting_age(self, user_id: int) -> bool:
        """Проверяет, ожидает ли пользователь ввод возраста"""
        return user_id in self.temp_states['awaiting_age']

    def clear_awaiting_age(self, user_id: int) -> None:
        """Снимает отметку ожидания ввода возраста"""
        self.temp_states['awaiting_age'].discard(user_id)

    # ----- Кастомная жалоба -----
    def set_custom_complaint(self, user_id: int, partner_id: int, chat_token: str = None) -> None:
        """
        Сохраняет состояние для кастомной жалобы.
        user_id: кто пишет жалобу
        partner_id: на кого жалуется
        chat_token: токен чата (для привязки)
        """
        self.temp_states['custom_complaint'][user_id] = {
            'partner_id': partner_id,
            'chat_token': chat_token
        }

    def get_custom_complaint(self, user_id: int) -> Optional[dict]:
        """Возвращает состояние кастомной жалобы для пользователя"""
        return self.temp_states['custom_complaint'].get(user_id)

    def clear_custom_complaint(self, user_id: int) -> None:
        """Удаляет состояние кастомной жалобы"""
        self.temp_states['custom_complaint'].pop(user_id, None)

    def has_custom_complaint(self, user_id: int) -> bool:
        """Проверяет, есть ли активное состояние кастомной жалобы"""
        return user_id in self.temp_states['custom_complaint']
