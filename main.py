# main.py
import asyncio
import logging
from src.telethone_client.telethone_client_bot import MainTelegramClient
from config import API_ID, API_HASH, SESSION_NAME, SYSTEM_VERSION, LOG_LEVEL


async def main():
    # Настройка логирования
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    logger.info("Инициализация телеграм клиента...")
    client = MainTelegramClient(
        API_ID,
        API_HASH,
        SESSION_NAME,
        system_version=SYSTEM_VERSION,
    )
    # Запускаем клиент
    try:
        logger.info("Запуск телеграм клиента...")
        await client.start()
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}", exc_info=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Получен сигнал прерывания. Завершение работы...")
        exit(0)
