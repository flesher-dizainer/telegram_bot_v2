import logging
from telethon import events, TelegramClient

class BaseHandlers:
    """Базовые обработчики для всех типов клиентов"""

    def __init__(self):
        pass

    async def handle_private_message(self, event: events.NewMessage.Event) -> None:
        logging.info('Отсутствует метод обработки приватных сообщений!')
        return None

    async def handle_group_message(self,event: events.NewMessage.Event) -> None:
        logging.info('Отсутствует метод обработки групповых сообщений!')
        return None

    async def handle_command(self, event: events.NewMessage.Event) -> None:
        logging.info('Отсутствует метод обработки команд!')
        return None
