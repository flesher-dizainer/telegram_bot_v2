import logging
from telethon import TelegramClient, events

from src.task_container import MessageProcessor
from src.telethone_client.handlers.base_handlers import BaseHandlers
from src.telethone_client.handlers.main_handlers import MainHandlers

# Базовый класс для работы с телеграм клиентом.
class BaseTelegramClient:
    """Базовый класс для работы с телеграм клиентом."""

    def __init__(self, api_id, api_hash, session_name, system_version='4.16.30-debian'):
        self.client = TelegramClient(session_name, api_id, api_hash, system_version=system_version)
        # Mistral AI
        self.handlers = BaseHandlers()

    async def start(self):
        async with self.client:
            logging.info("Telegram client started")

            # Регистрируем обработчик приватных сообщений
            @self.client.on(
                events.NewMessage(func=lambda e: e.is_private & (not e.message.text.strip().startswith('/'))))
            async def handler_private(event):
                await self.handlers.handle_private_message(event=event)

            # Регистрируем обработчик групповых сообщений
            @self.client.on(events.NewMessage(func=lambda e: e.is_group))
            async def handler_group(event):
                await self.handlers.handle_group_message(event=event)

            # Регистрируем обработчик команд
            @self.client.on(events.NewMessage(func=lambda e: e.is_private & e.message.text.strip().startswith('/')))
            async def handler_command(event:events.NewMessage.Event):
                await self.handlers.handle_command(event=event)

            # Запускаем клиент
            try:
                await self.client.run_until_disconnected()
            except KeyboardInterrupt:
                logging.info("Получен сигнал прерывания. Завершение работы...")
                # raise KeyboardInterrupt('Программа завершена пользователем')


class MainTelegramClient(BaseTelegramClient):

    def __init__(self, api_id, api_hash, session_name, system_version='4.16.30-debian'):
        super().__init__(api_id, api_hash, session_name, system_version)

        # handlers
        self.handlers = MainHandlers()
        self.logger = logging.getLogger(__name__)

    async def start(self):
        """Запускает планировщик задач и клиент."""
        await self.handlers.task_scheduler.start()
        # добавляем задачу на обработку групповых сообщений
        await self.handlers.task_scheduler.add_task(MessageProcessor.processing_loop())
        # активируем задачу
        await self.handlers.task_scheduler.run_all_pending()
        await super().start()  # Запускаем клиент
