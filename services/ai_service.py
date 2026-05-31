# services/ai_service.py
"""
Сервис для работы с AI-собеседником.

Поддерживает любые API совместимые с OpenAI форматом:
- OpenRouter
- Arcee AI
- Локальные сервера (LiteRT-LM, llama.cpp)
"""

import aiohttp
import asyncio
import logging
import random
import json
from typing import Optional, Dict, List, Any

from config import settings
from repositories.user_repo import UserRepo
from repositories.ai_repo import AIRepo

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # принудительно

class AIService:
    """Сервис для управления AI-собеседником"""

    def __init__(self, user_repo: UserRepo, ai_repo: AIRepo):
        """
        Инициализация AI сервиса.

        :param user_repo: репозиторий пользователей
        :param ai_repo: репозиторий AI
        """
        self.user_repo = user_repo
        self.ai_repo = ai_repo
        # self._load_settings()
        # Запускаем загрузку настроек в фоне
        asyncio.create_task(self._load_settings())

    async def _load_settings(self):
        """Загружает настройки AI из БД"""
        settings = await self.ai_repo.get_settings()  # ← добавить await
        self.ai_enabled = settings.get('ai_enabled', '1') == '1'
        self.ai_timeout = int(settings.get('ai_timeout', '15'))
        self.default_model = settings.get('default_model', 'nvidia/nemotron-3-nano-30b-a3b:free')
        self.max_free_messages = int(settings.get('max_free_messages', '50'))
        self.temperature = float(settings.get('temperature', '0.9'))
        self.max_tokens = int(settings.get('max_tokens', '400'))
        self.top_p = float(settings.get('top_p', '0.9'))
        self.frequency_penalty = float(settings.get('frequency_penalty', '0.3'))
        self.presence_penalty = float(settings.get('presence_penalty', '0.2'))

    # def _load_settings(self):
    #     """Загружает настройки AI из БД"""
    #     settings = self.ai_repo.get_settings()
    #     self.ai_enabled = settings.get('ai_enabled', '1') == '1'
    #     self.ai_timeout = int(settings.get('ai_timeout', '15'))
    #     self.default_model = settings.get('default_model', 'nvidia/nemotron-3-nano-30b-a3b:free')
    #     self.max_free_messages = int(settings.get('max_free_messages', '50'))
    #     self.temperature = float(settings.get('temperature', '0.9'))
    #     self.max_tokens = int(settings.get('max_tokens', '400'))
    #     self.top_p = float(settings.get('top_p', '0.9'))
    #     self.frequency_penalty = float(settings.get('frequency_penalty', '0.3'))
    #     self.presence_penalty = float(settings.get('presence_penalty', '0.2'))

    def refresh_settings(self):
        """Обновляет настройки из БД (для админки)"""
        self._load_settings()

    def get_active_model(self) -> Dict:
        """Возвращает активную модель из БД"""
        model = self.ai_repo.get_active_model()
        if not model:
            # Возвращаем дефолтную
            return {
                'name': self.default_model,
                'max_tokens': self.max_tokens,
                'temperature': self.temperature,
                'top_p': self.top_p,
                'frequency_penalty': self.frequency_penalty,
                'presence_penalty': self.presence_penalty
            }
        return model

    # ================================================================
    # ВЫБОР ПЕРСОНАЖА
    # ================================================================

    async def get_ai_character(self, gender_filter: str = "normal", user_topics: list = None, user_gender: str = "unknown", user_lang: str = "ru") -> dict:
        """
        Универсальный метод подбора ИИ-персонажа (по вашей вилке).
        Если темы переданы — идет отбор по ним.
        Если тем нет или по ним в БД пусто — выгребает любого персонажа нужного пола и языка.
        """
        import random
        import json
        from lang import get_message
        character = None

        is_general_flood = (gender_filter == "normal")
        topics_list = user_topics or []

        # 1. ОТБОР ПО ТОПИКАМ И ПОЛУ (если список тем не пуст)
        if topics_list and not is_general_flood:
            chosen_topic_id = random.choice(topics_list)
            topic_info = await self.topic_repo.get_topic_by_id(chosen_topic_id)

            if topic_info:
                target_topic_name = topic_info.get('name', 'general_chat')
                character = await self.ai_repo.get_character_by_topic(target_topic_name, gender_filter, user_lang)

        # 2. ОБЩИЙ ОТБОР (если флуд или по теме в БД пусто)
        if not character:
            character = await self.ai_repo.get_all_characters(gender_filter, user_lang)

        # 3. ЖЕСТКАЯ СТРАХОВКА ТИПА (Схлопываем любой массив из репозитория в один словарь)
        if isinstance(character, list):
            if len(character) > 0:
                character = random.choice(character)
            else:
                character = {}

        # 4. РАСПАКОВКА ИМЕНИ ИЗ JSON (С фолбеком через движок i18n)
        raw_names = character.get('names')
        ai_name = None
        if raw_names:
            try:
                names_list = json.loads(raw_names)
                if names_list:
                    ai_name = random.choice(names_list)
            except Exception:
                pass

        if not ai_name:
            ai_name = get_message('ai_anonymous', lang=user_lang)

        # Генерируем случайный возраст в рамках лимитов персонажа
        ai_age = random.randint(character.get('min_age', 18), character.get('max_age', 30))

        # 5. СБОРКА СИСТЕМНОГО ПРОМПТА ЧЕРЕЗ ШАБЛОН ИЗ ЯЗЫКОВОГО ФАЙЛА (БЕЗ ХАРДКОДА)
        base_prompt = get_message(
            'ai_base_prompt_template',
            lang=user_lang,
            name=ai_name,
            age=ai_age,
            traits=character.get('traits', ''),
            style=character.get('style', ''),
            rules=character.get('rules', ''),
            extra_prompt=character.get('prompt', '') or ''
        )

        # 6. ДИНАМИЧЕСКАЯ СКЛЕЙКА МЕТА-ПРОМПТА ИЗ АДМИНКИ С ВАШИМ СИСТЕМНЫМ КЛЮЧОМ ai_
        if is_general_flood:
            setting_key = f"general_chat_rules_{user_lang.lower()}"
            i18n_fallback = get_message('ai_general_chat_rules', lang=user_lang)

            general_meta_rules = await self.ai_repo.get_setting(setting_key, default=i18n_fallback)
            final_prompt = f"{general_meta_rules}\n\n{base_prompt}"
        else:
            final_prompt = base_prompt

        # Выставляем строгий латинский флаг-маркер темы
        db_topic = character.get('topic', 'general_chat')
        res_topic = "general_chat" if is_general_flood else db_topic

        return {
            "id": character.get('id'),
            "name": ai_name,
            "topic": res_topic,  # Строгий латинский slug для конвейера
            "gender": character.get('gender', 'unknown'),
            "prompt": final_prompt
        }

    # ================================================================
    # УПРАВЛЕНИЕ СЕССИЯМИ
    # ================================================================

    # Обновленный метод внутри класса AIService в ai_service.py

    async def start_session(self, user_id: int, user_gender: str, user_topics: list, user_lang: str) -> dict:
        """
        Начинает мультиязычную AI сессию для пользователя по таймауту из очереди.
        НИКАКОГО SQL: Только координация вызовов репозиториев и кэширование в ОЗУ.

        Вход: Данные пользователя, которые конвейер УЖЕ хранит в ОЗУ.
        Выход: Карточка подобранного ИИ-персонажа (dict) для отправки сообщений в UI.
        """
        # 1. Подбираем случайного ИИ-персонажа через наш универсальный мультиязычный метод
        character = await self.get_ai_character(
            gender_filter="normal",
            user_topics=user_topics,
            user_gender=user_gender,
            user_lang=user_lang
        )

        if not character or not character.get('id'):
            logger.warning(f"[AI_START_FAIL] Не удалось подобрать персонажа для {user_id}. База пуста?")
            return {}

        # 2. Создаем чат в active_chats. Метод репозитория сам сгенерирует UUID и вернет его.
        # Маскируем ИИ под партнера с отрицательным ID (-character_id)
        chat_token = await self.chat_repo.create_active_chat(
            user1_id=user_id,
            user2_id=-character['id']
        )

        # 3. Фиксируем сессию в таблице ai_sessions_log на диске, привязывая её к chat_token
        # (Замените log_session_start на create_ai_session, если переименовали метод в ai_repo.py)
        await self.ai_repo.create_ai_session(
            chat_token=chat_token,
            user_id=user_id,
            character_id=character['id']
        )

        # 4. Инициализируем пустую историю контекста сообщений нейросети в ОЗУ
        self._ai_histories[user_id] = []

        logger.info(f"[AI_START_SUCCESS] Чат начат для {user_id} с персонажем {character['name']} (Токен: {chat_token})")

        # Возвращаем готовую карточку персонажа, чтобы конвейер поиска отправил красивое UI-сообщение
        return character


    async def end_session(self, user_id: int) -> None:
        """
        Завершает AI сессию пользователя, очищает ОЗУ и фиксирует лог в истории.
        ИСПРАВЛЕНО: SQL-запрос полностью перенесен в репозиторий.
        """
        try:
            # 1. Стираем привязку скрытого робота в таблице users
            await self.user_repo.update_user_ai_character(user_id, None)

            # 2. Удаляем историю из быстрой памяти ОЗУ, освобождая ресурсы сервера
            if user_id in self._ai_histories:
                del self._ai_histories[user_id]

            # 3. ПРЯМАЯ ТРАССА: Просим репозиторий зафиксировать время закрытия в БД
            await self.ai_repo.log_session_end(user_id)

            logger.info(f"AI-чат завершён для пользователя {user_id}")

        except Exception as e:
            logger.error(f"Ошибка при закрытии ИИ сессии для пользователя {user_id}: {e}")

    # ================================================================
    # ОТПРАВКА СООБЩЕНИЙ В AI
    # ================================================================

    async def send_message(self, user_id: int, message_text: str) -> str:
        """
        Отправляет сообщение AI и возвращает ответ.

        :return: текст ответа AI или код ошибки
        """
        # Проверяем лимит сообщений для бесплатных пользователей
        if not self._can_send_message(user_id):
            return "AI_ERROR_LIMIT"

        # Получаем историю диалога
        history = self.universe.get_ai_history(user_id)
        if history is None:
            logger.warning(f"Нет AI сессии для {user_id}")
            return "AI_ERROR"

        # Добавляем сообщение пользователя в историю
        history.append({"role": "user", "content": message_text})
        self.universe.increment_ai_messages_count(user_id)

        # Обрезаем историю, если слишком длинная
        self.universe.truncate_ai_history(user_id, max_messages=21)

        # Отправляем запрос к AI API
        reply = await self._call_ai_api(history)

        if reply is None:
            return "AI_ERROR"

        # Очищаем ответ от возможных мета-комментариев
        reply = self._clean_response(reply)

        # Добавляем ответ AI в историю
        history.append({"role": "assistant", "content": reply})

        return reply

    def _can_send_message(self, user_id: int) -> bool:
        """
        Проверяет, может ли пользователь отправить сообщение AI.

        Ограничения:
        - Премиум — безлимит
        - Бесплатные — до MAX_FREE_AI_MESSAGES
        """
        # Проверяем премиум
        if self.user_repo.is_premium(user_id):
            return True

        # Проверяем лимит сообщений
        messages_count = self.universe.get_ai_messages_count(user_id)
        return messages_count < self.max_free_messages

    # services/ai_service.py (добавить метод generate_reply)

    async def generate_reply(self, user_id: int, message_text: str) -> str:
        """
        Генерирует ответ AI для пользователя.
        """
        # Получаем активную сессию AI для пользователя
        session = await self._get_or_create_session(user_id)

        if not session:
            return get_error('ai_error')

        # Добавляем сообщение пользователя в историю
        session['history'].append({'role': 'user', 'content': message_text})

        # Отправляем запрос к AI API
        reply = await self._call_ai_api(session['history'])

        if reply is None:
            return get_error('ai_error')

        # Добавляем ответ в историю
        session['history'].append({'role': 'assistant', 'content': reply})

        return reply

    async def _call_ai_api(self, history: list) -> Optional[str]:

        """Отправляет контекст в API, используя ai_timeout для контроля сети"""

        # Считываем сетевые параметры из вашей таблицы
        api_url = await self.ai_repo.get_setting('ai_api_url', 'https://openrouter.ai')
        api_key = await self.ai_repo.get_setting('ai_api_key', '')

        # ИСПРАВЛЕНО: Читаем ваш ключ ai_timeout из БД (время ожидания ответа движка)
        db_timeout_str = await self.ai_repo.get_setting('ai_timeout', default='15')
        engine_timeout_sec = int(db_timeout_str)

        # Считываем параметры генерации
        model_name = await self.ai_repo.get_setting('default_model', 'nvidia/nemotron-3-nano-30b-a3b:free')
        db_temp = float(await self.ai_repo.get_setting('temperature', '0.9'))
        db_tokens = int(await self.ai_repo.get_setting('max_tokens', '400'))
        db_top_p = float(await self.ai_repo.get_setting('top_p', '0.9'))
        db_freq = float(await self.ai_repo.get_setting('frequency_penalty', '0.3'))
        db_pres = float(await self.ai_repo.get_setting('presence_penalty', '0.2'))

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model_name,
            "messages": history,
            "temperature": db_temp,
            "max_tokens": db_tokens,
            "top_p": db_top_p,
            "frequency_penalty": db_freq,
            "presence_penalty": db_pres
        }

        try:
            # ПРИМЕНЯЕМ ТАЙМАУТ ДВИЖКА: Передаем секунды из базы данных!
            client_timeout = aiohttp.ClientTimeout(total=engine_timeout_sec)

            async with aiohttp.ClientSession(timeout=client_timeout) as session:
                async with session.post(api_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        result_json = await response.json()
                        return result_json['choices']['message']['content']
                    else:
                        logger.error(f"[AI_API] Ошибка движка {model_name}. Статус: {response.status}")
                        return None

        except asyncio.TimeoutError:
            # Если движок превысил время ожидания ai_timeout из БД
            logger.error(f"[AI_API] Движок нейросети таймаутнул после {engine_timeout_sec} сек ожидания!")
            # TODO: Здесь в будущем будет вызов метода ротации (fallback_to_next_model)
            return None
        except Exception as e:
            logger.error(f"[AI_API] Ошибка сети при запросе к ИИ: {e}")
            return None


#     async def _call_ai_api(self, messages: List[Dict]) -> Optional[str]:
#         """
#         Отправляет запрос к AI API (OpenRouter, Arcee, локальный сервер).
#
#         Формат запроса — совместим с OpenAI API.
#
#         :return: ответ AI или None при ошибке
#         """
#         if not AI_API_KEY:
#             logger.error("AI_API_KEY не настроен")
#             return None
#
#         model_config = self.get_active_model()
#
#         headers = {
#             "Authorization": f"Bearer {AI_API_KEY}",
#             "Content-Type": "application/json"
#         }
#
#         payload = {
#             "model": model_config['name'],
#             "messages": messages,
#             "max_tokens": model_config.get('max_tokens', self.max_tokens),
#             "temperature": model_config.get('temperature', self.temperature),
#             "top_p": model_config.get('top_p', self.top_p),
#             "frequency_penalty": model_config.get('frequency_penalty', self.frequency_penalty),
#             "presence_penalty": model_config.get('presence_penalty', self.presence_penalty)
#         }
#
#         try:
#             async with aiohttp.ClientSession() as session:
#                 async with session.post(AI_API_URL, json=payload, headers=headers) as resp:
#                     if resp.status == 200:
#                         data = await resp.json()
#                         reply = data.get("choices", [{}])[0].get("message", {}).get("content")
#
#                         if reply and reply.strip():
#                             logger.info(f"[AI] Ответ получен, длина: {len(reply)}")
#                             return reply.strip()
#                         else:
#                             logger.warning("[AI] Пустой ответ от AI API")
#                             return None
#                     else:
#                         error_text = await resp.text()
#                         logger.error(f"[AI] AI API ошибка {resp.status}: {error_text}")
#                         return None
#
#         except aiohttp.ClientError as e:
#             logger.error(f"[AI] Ошибка HTTP: {e}")
#             return None
#         except Exception as e:
#             logger.error(f"[AI] Неизвестная ошибка: {e}")
#             return None

    async def _call_ai_api(self, messages: List[Dict], retry: int = 2) -> Optional[str]:
        """
        Отправляет запрос к AI API (OpenRouter, Arcee, локальный сервер) с повторными попытками.
        Формат запроса — совместим с OpenAI API.
        :return: ответ AI или None при ошибке
        """
        if not settings.ai_api_key:
            logger.error(f"[AI] API ключ не настроен: {settings.ai_api_key}")
            return None

        model_config = self.get_active_model()

        headers = {
            "Authorization": f"Bearer {settings.ai_api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model_config['name'],
            "messages": messages,
            "max_tokens": model_config.get('max_tokens', self.max_tokens),
            "temperature": model_config.get('temperature', self.temperature),
            "top_p": model_config.get('top_p', self.top_p),
            "frequency_penalty": model_config.get('frequency_penalty', self.frequency_penalty),
            "presence_penalty": model_config.get('presence_penalty', self.presence_penalty)
        }

        for attempt in range(retry + 1):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(settings.ai_api_url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            reply = data.get("choices", [{}])[0].get("message", {}).get("content")
                            if reply and reply.strip():
                                logger.info(f"[AI] Ответ получен, длина: {len(reply)}")
                                logger.debug(f"[AI] Body: {json.dumps(data, ensure_ascii=False)[:500]}")
                                return reply.strip()
                            else:
                                logger.warning(f"[AI] Пустой ответ, попытка {attempt + 1}/{retry + 1}")
                                logger.debug(f"[AI] Body: {json.dumps(data, ensure_ascii=False)}")
                                await asyncio.sleep(1)
                        else:
                            error_text = await resp.text()
                            logger.error(f"[AI] Ошибка {resp.status}, попытка {attempt + 1}/{retry + 1}: {error_text}")
                            await asyncio.sleep(2)

            except asyncio.TimeoutError:
                logger.warning(f"[AI] Таймаут, попытка {attempt + 1}/{retry + 1}")
                await asyncio.sleep(2)

            except aiohttp.ClientError as e:
                logger.error(f"[AI] Ошибка HTTP: {e}")
                return None

            except Exception as e:
                logger.error(f"[AI] Ошибка: {e}, попытка {attempt + 1}/{retry + 1}")
                await asyncio.sleep(2)

        return None

    def _clean_response(self, text: str) -> str:
        """
        Очищает ответ AI от мета-комментариев.

        Удаляет:
        - Текст в скобках (описания действий)
        - Текст в квадратных скобках
        """
        import re

        # Удаляем текст в круглых скобках
        text = re.sub(r'\s*\([^)]*\)\s*', ' ', text)
        # Удаляем текст в квадратных скобках
        text = re.sub(r'\s*\[[^\]]*\]\s*', ' ', text)
        # Убираем лишние пробелы
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    # ================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ================================================================

    def get_character_name(self, user_id: int) -> str:
        """Возвращает имя AI персонажа для пользователя"""
        character = self.universe.get_ai_character(user_id)
        return character.get('name', 'Аноним') if character else 'Аноним'

    def get_profile(self, user_id: int) -> Optional[Dict]:
        """
        Возвращает профиль AI-собеседника для отображения.
        Используется при нажатии кнопки "👤 Профиль" в AI-чате.
        """
        character = self.universe.get_ai_character(user_id)
        if not character:
            return None

        return {
            "chat_name": character.get('name'),
            "age": character.get('age'),
            "gender": character.get('gender'),
            "topics": [character.get('topic', 'Общение')],
            "is_ai": True
        }
