import logging
from telethon import events
from telethon.tl.functions.channels import JoinChannelRequest

from src.task_manager import TaskScheduler
from src.telethone_client.handlers.base_handlers import BaseHandlers
from src.task_container.tasks import TaskContainer, MessageProcessor


class MainHandlers(BaseHandlers):
    """Обработчики для главного клиента"""

    def __init__(self):
        super().__init__()
        self.task_scheduler = TaskScheduler()
        self.task_container = TaskContainer()

    async def handle_group_message(self, event: events.NewMessage.Event) -> None:
        """Обработчик групповых сообщений"""
        await MessageProcessor.add_message(event)

    async def handle_command(self, event: events.NewMessage.Event) -> None:
        """Обработчик команд"""
        if not hasattr(event, 'message') or not event.message.text:
            return
        try:
            command = event.message.text.lower().split()[0].strip()
        except IndexError:
            return
        if command == '/help':
            await self.help_command(event)
        elif command == '/start_pars':
            await self.handle_pars_command(event)
        elif command == '/get_status':
            await self.handle_status_tasks(event)
        elif command == '/get_prompt_msg':
            await self.get_prompt_filter(event)
        elif command == '/set_prompt_msg':
            await self.set_prompt_filter(event)
        elif command == '/join_groups':
            await self.handle_join_groups(event)
        else:
            await self.handle_no_command(event)

    async def help_command(self, event: events.NewMessage.Event) -> None:
        """Обработчик команды /help"""
        text = ('Доступные команды:\n'
                '/start_pars - запуск парсинга групп. Добавить нельзя пока.\n'
                '/get_status - возвращает статус задач\n'
                '/get_prompt_msg - запросить промпт фильтрации сообщений\n'
                '/set_prompt_msg - задать промпт фильтрации сообщений. Нужно выбрать файл с названием prompt_message.txt\n'
                '/join_groups - вступить в группы')
        await event.reply(text)

    async def handle_pars_command(self, event: events.NewMessage.Event) -> None:
        """Обработчик команды /start"""
        logging.info("Добавляем задачу на парсинг групп")
        id_task = await self.task_scheduler.add_task(self.task_container.parse_groups(event.client, event),
                                                     "parsing_groups")
        # await  self.task_scheduler.run_all_pending()
        await self.task_scheduler.run_task(id_task)
        logging.info(f'Задача запущена: {id_task}')
        all_tasks = self.task_scheduler.task_status(id_task.id)
        logging.info(f'Все задачи: {all_tasks}')
        await event.reply('Задача парсинга групп запущена')

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

    async def get_prompt_filter(self, event: events.NewMessage.Event):
        """Получает текст из сообщения и возвращает его"""
        try:
            path_file = 'src/prompts/prompt_message.txt'
            await event.client.send_file(event.message.chat_id, path_file, force_document=True,
                                         caption="Промпт фильтра сообщений")
        except Exception as e:
            logging.error(f"Ошибка при отправке сообщения: {e}")

    async def set_prompt_filter(self, event: events.NewMessage.Event):
        message = event.message
        client = event.client
        if message.file:
            file_path = f'src/prompts/{message.file.name}'
            await client.download_media(message, file_path)
            await client.send_message(message.chat_id, f"Файл {file_path} успешно загружен.")
        else:
            await client.send_message(message.chat_id, "Пожалуйста, отправьте файл.")

    async def handle_join_groups(self, event: events.NewMessage.Event):
        logging.info('Добавляем задачу на вступление в группы')
        id_task = await self.task_scheduler.add_task(self.task_container.join_group_or_channel(event),
                                                     "join_groups")
        await self.task_scheduler.run_task(id_task)
