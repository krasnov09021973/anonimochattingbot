# /config.py
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Telegram
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле")

# AI настройки
AI_ENABLED = os.getenv("AI_ENABLED", "True").lower() == "true"
AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "15"))  # секунд до подключения AI
MAX_FREE_AI_MESSAGES = 50
AI_API_KEY = os.getenv('AI_API_KEY')  # API ключ для AI сервиса (OpenRouter, Arcee, и т.д.)
# Базовый URL для API (может быть OpenRouter, Arcee, локальный сервер)
AI_API_URL = os.getenv('AI_API_URL', 'https://openrouter.ai/api/v1/chat/completions')

# Администраторы (Telegram ID)
ADMIN_IDS = os.getenv('ADMIN_IDS', '').split(',')
ADMIN_IDS = [uid.strip() for uid in ADMIN_IDS if uid.strip()]

# Базовый путь проекта
BASE_DIR = Path(__file__).parent

# Пути к данным
DB_PATH = BASE_DIR / 'data' / 'anon_chat.db'
LOG_DIR = BASE_DIR / 'data' / 'logs'

# Создаем папки если их нет
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DB_PATH.parent, exist_ok=True)

# Лимиты (по умолчанию)
DAILY_LIMIT_GUEST = 5        # гость (до 50 чатов) или репутация 0-25
DAILY_LIMIT_USER = 10        # обычный пользователь, репутация 25-50
DAILY_LIMIT_TRUSTED = 20     # репутация 50-100
DAILY_LIMIT_VIP = 999        # премиум

# Возрастные ограничения
MIN_AGE = 12
MAX_AGE = 99

# Оплата ПРЕМИУМ в звездах и деньгах (рублях)
VIP_STARS_WEEK = 100
VIP_STARS_MONTH = 250
VIP_STARS_HALFYEAR = 750
VIP_STARS_FULLYEAR = 1000
VIP_PAY_WEEK = 199
VIP_PAY_MONTH = 499
VIP_PAY_HALFYEAR = 1499
VIP_PAY_FULLYEAR = 1899
