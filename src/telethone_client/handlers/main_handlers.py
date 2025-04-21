import logging
from telethon import events

from src.task_manager import TaskScheduler
from src.telethone_client.handlers.base_handlers import BaseHandlers
from src.task_container.tasks import TaskContainer


class MainHandlers(BaseHandlers):
    """Обработчики для главного клиента"""

    def __init__(self):
        super().__init__()
        self.task_scheduler = TaskScheduler()
        self.task_container = TaskContainer()

    async def handle_group_message(self, event: events.NewMessage.Event) -> None:
        """Обработчик групповых сообщений"""
        logging.info('Метод обработки групповых сообщений не реализован!')

    async def handle_command(self, event: events.NewMessage.Event) -> None:
        """Обработчик команд"""
        if not hasattr(event, 'message') or not event.message.text:
            return

        try:
            command = event.message.text.lower().split()[0].strip()
        except IndexError:
            return
        if command == '/start_pars':
            await self.handle_pars_command(event)
        else:
            await self.handle_no_command(event)


    async def handle_pars_command(self, event: events.NewMessage.Event) -> None:
        """Обработчик команды /start"""
        logging.info("Добавляем задачу на парсинг групп")
        id_task = await self.task_scheduler.add_task(self.task_container.parse_groups(event.client, event), "parsing_groups")
        await  self.task_scheduler.run_all_pending()
        logging.info(f'Задача запущена: {id_task}')
        all_tasks = self.task_scheduler.task_status(id_task.id)
        logging.info(f'Все задачи: {all_tasks}')
        await event.reply('Привет! Я бот для управления задачами. Используйте /help для просмотра доступных команд.')

    async def handle_status_tasks(self, event: events.NewMessage.Event) -> None:
        """Обработчик команды /get_status"""
        logging.info('Получена команда /get_status')
        all_tasks = self.task_scheduler.get_all_tasks()
        for task in all_tasks:
            logging.info(f'Задача: {task.name} - {task.status}')
        text = '\n'.join([f'Задача: {task.name} - {task.status} \n' for task in all_tasks])
        await event.reply(f'Все задачи: {text}')

    async def handle_no_command(self, event: events.NewMessage.Event) -> None:
        """Обработчик отсутствующих команд"""
        await event.reply('Команда не найдена. Используйте /help для просмотра доступных команд.')
