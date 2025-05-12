import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Telegram API
API_ID = int(os.getenv('TELEGRAM_API_ID', '0'))
API_HASH = os.getenv('TELEGRAM_API_HASH', '')
SESSION_NAME = os.getenv('TELEGRAM_SESSION_NAME', 'tg_session')
SYSTEM_VERSION = os.getenv('TELEGRAM_SYSTEM_VERSION', '4.16.30-debian')

# Mistral AI
MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY', '')
MISTRAL_API_MODEL = os.getenv('MISTRAL_API_MODEL', 'mistral-tiny')
MISTRAL_API_KEY_PARSING_GROUP = os.getenv('MISTRAL_API_KEY_PARSING_GROUP', '')

# Database
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///src/telegram_clients.db')

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Имя пользователя, кому пересылаем сообщения
FORWARD_CHAT_ID = os.getenv('FORWARD_CLIENT_USERNAME', '').split(',')
