import asyncio
from datetime import datetime, timedelta, timezone
from typing import List

from telethon.tl.functions.channels import JoinChannelRequest

from src.utils.json_utils import JsonUtils

from telethon import TelegramClient, events, errors
from src.database.database import Database
from config import DATABASE_URL, MISTRAL_API_KEY, MISTRAL_API_MODEL, MISTRAL_API_KEY_PARSING_GROUP, FORWARD_CHAT_ID
import logging
from src.utils.mistralAi import MistralAI, get_count_message

PROMPT = """
                    Ты — модель для классификации сообщений на три категории: спам, обычные и рекламные. Критерии:
                    
                    1. **Спам:**
                       - Фишинговые ссылки, сомнительные предложения, повторяющиеся сообщения.
                       - Слова вроде "выиграйте", "бесплатно", "только сегодня", "скрытые комиссии", "Оцени меня".
                       - Много ошибок или плохая грамматика.
                    
                    2. **Обычные:**
                       - Личные сообщения, рабочие задачи, вопросы.
                       - Сообщения о продаже товаров/услуг **без** призывов к покупке (например: "Продаю диван", "Делаю сайты под ключ").
                       - Контактные данные для заказа (например: "Мой номер для связи: +7...").
                       - Любые сообщения без спама и рекламных призывов.
                    
                    3. **Рекламные:**
                       - Акции, скидки, новые продукты (например: "Скидка 50%!", "Новинка 2024!").
                       - Явные призывы к действию: "купите сейчас", "закажите", "подпишитесь", "узнайте больше".
                       - Сообщения, продвигающие товары/услуги через маркетинговые уловки.
                    
                    Примеры классификации:
                    1. "Заберите свой выигрыш по ссылке [phishing.link]" → Спам
                    2. "Привет, готов обсудить проект" → Обычные
                    3. "Продаю велосипед, звоните: +7..." → Обычные
                    4. "Скидка 30% на курс! Успейте купить!" → Рекламные
                    
                    Если есть хотя бы одно обычное сообщение, верни:
                    - `"group": true` 
                    - `"count_message": [количество]`
                    Иначе — `"group": false` и `"count_message": 0`.
"""


class TaskContainer:
    """Класс-контейнер для хранения задач"""

    @staticmethod
    async def parse_groups(client: TelegramClient, event: events.NewMessage.Event) -> None:
        """
        Парсинг групп
        :param : client: TelegramClient, event: events
        :return: None
        """
        # нужно открыть текстовый файл prompt для mistral
        try:
            with open('../prompts/prompt_mistral.txt', 'r', encoding='utf-8') as file:
                prompt = file.read()
        except FileNotFoundError:
            logging.info("Файл 'prompt_mistral.txt' не найден.")
            prompt = PROMPT
        mistral_client = MistralAI(MISTRAL_API_KEY_PARSING_GROUP, MISTRAL_API_MODEL)
        db = Database(DATABASE_URL)
        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        try:
            # принимаем данные из бд
            chats_db = (await db.get_chats_by_status(status='test'))
            await event.reply(f"Количество чатов для парсинга: {len(chats_db)}")
            for chat in chats_db:
                try:
                    messages = await client.get_messages(chat.name, limit=10)
                    # Обработка сообщений через мистраль
                    message_list = ''
                    list_messages = []
                    for message in messages:
                        if message.text and (message.date >= twenty_four_hours_ago):
                            message_list += f"id:{message.sender_id}, message: {message.message}\n"
                            list_messages.append(message.sender_id)
                    if list_messages:
                        try:
                            text_mistral = await mistral_client.chat(message_list, prompt)
                            logging.info(f'Mistral: {text_mistral}')
                            count_message_mistral = await get_count_message(text_mistral)
                            if count_message_mistral > 3:
                                logging.info(f"group: {chat.name}, status: second")
                                await db.update_group_chat(chat.id, status='second')
                            else:
                                await db.update_group_chat(chat.id, status='bad_second')
                                logging.info(f"group: {chat.name}, status: bad second")
                        except Exception as e:
                            logging.info(f'Ошибка Mistral{e}')
                    else:
                        await db.update_group_chat(chat.id, status='bad_second')
                        continue
                except errors.FloodWaitError as e:
                    logging.error(f"Ошибка: {e}")
                    await event.reply(f"Ошибка FloodWaitError: {e.seconds}")
                    await asyncio.sleep(e.seconds)
                    continue
                except Exception as e:
                    logging.error(f"Ошибка: {e}")
                    await db.update_group_chat(chat.id, status='bad')
        except Exception as e:
            logging.error(f"Ошибка при работе с бд: {e}")
            return
        finally:
            logging.info("Закрытие подключения к бд")
            await db.close()
            logging.info("Парсинг групп завершен")
            await event.reply("Парсинг групп завершен")

    @staticmethod
    async def join_group_or_channel(event: events.NewMessage.Event):
        """Присоединяется к группе или чату."""
        # получаем из бд все группы и каналы со статусом second
        await event.reply("Присоединяюсь к группам и каналам...")
        db = Database(DATABASE_URL)
        try:
            # получаем список групп и каналов из бд
            groups_list = await db.get_chats_by_status(status='second')
            # получаем список всех подключенных групп
            connected_groups = await event.client.get_dialogs()
            # формируем список id подключенных групп
            connected_groups_ids = [group.id for group in connected_groups]
            count_groups_connect = 0
            for group in groups_list:
                try:
                    channel = await event.client.get_entity(group.name)
                    if channel.id not in connected_groups_ids:
                        await event.client(JoinChannelRequest(channel))
                        await asyncio.sleep(60 * 5)
                    # меняем статус группы в бд на 'connected'
                    await db.update_group_chat(group.id, status='connected')
                except errors.FloodWaitError as e:
                    logging.error(f"Ошибка: {e}")
                    await event.reply(f"Ошибка FloodWaitError: {e.seconds}")
                    await asyncio.sleep(e.seconds)
                    continue
                except Exception as e:
                    logging.info("Ошибка при присоединении к группе или чату: " + str(e))
        except Exception as e:
            logging.info("Ошибка при получении списка групп и каналов из БД: " + str(e))
        finally:
            await db.close()
            await event.reply("Присоединение к группам и каналам завершено")


class MessageProcessor:
    _messages_buffer: List[events.NewMessage.Event] = []
    _blocked_ids: [int] = set()
    _last_processed: datetime = datetime.now(timezone.utc)
    _processing_interval: int = 30  # Интервал обработки в секундах (1 минута)
    _lock = asyncio.Lock()
    _prompt_message_default = """
        Верни json. 
        Твоя задача определить спам, рекламу и так далее. Самое основное, это понять что сообщение подходит нашим критериям.
        Критерии:
            1. Человек ищет помощь в строительстве или консультацию по строительству дома, гаража, дачи, бани и т.д.
        В ответе всегда должен быть пункт "category". 
        category может иметь значения:
        - spam
        - advertising
        - offer_job
        - seeking_ok - подошло по нашим критериям
        - irrelevant – сообщение не относится к строительству.
        - scam – мошенничество или подозрительное предложение.
        - request_quote – запрос стоимости услуг.
        - partnership – предложение сотрудничества.
        - question – общий вопрос по строительству.
        - feedback – отзыв или комментарий о работе.
        - other – что-то ещё, не подходящее под основные категории.
        """

    @classmethod
    async def add_message(cls, event: events.NewMessage.Event) -> None:
        """Добавляет сообщение в буфер для последующей обработки."""
        async with cls._lock:
            cls._messages_buffer.append(event)

    @classmethod
    async def _process_buffered_messages(cls) -> None:
        """Обрабатывает все накопленные сообщения."""
        async with cls._lock:
            cls._last_processed = datetime.now(timezone.utc)

            if not cls._messages_buffer:
                logging.info("Буфер пуст, нет сообщений для обработки.")
                return
            _messages_buffer = cls._messages_buffer.copy()
            cls._messages_buffer.clear()

        # Здесь ваша логика обработки сообщений
        logging.info(f"Обрабатываю {len(_messages_buffer)} сообщений...")
        message_list = "{"
        count_message_mistral = 0
        for msg in _messages_buffer:
            if msg.sender_id not in cls._blocked_ids:
                count_message_mistral += 1
                message_list += f"Message id: {msg.id}, chanel_id: {msg.chat_id}, sender_id: {msg.sender_id}, text: {msg.text}\n"

        # Здесь вы можете выполнить любую логику обработки сообщений
        # print(msg.stringify())
        logging.info(f"Количество сообщений для обработки в Mistral: {count_message_mistral}")
        message_list += '}'

        try:
            with open('src/prompts/prompt_message.txt', 'r', encoding='utf-8') as file:
                prompt = file.read()
        except FileNotFoundError:
            logging.info("Файл 'prompt_message.txt' не найден.")
            prompt = cls._prompt_message_default

        mistral_client = MistralAI(MISTRAL_API_KEY, MISTRAL_API_MODEL)
        try:
            text_mistral = await mistral_client.chat(message_list, prompt)
            # print(text_mistral)
            # ПРЕОБРАЗУЕМ В JSON
            mistral_dict = JsonUtils.text_to_json(text_mistral)
            list_msg_dict = []
            if type(mistral_dict) is dict:
                # logging.info(f'Mistral: {mistral_dict}')
                status_msg = mistral_dict.get('category', None)
                if status_msg in ['scam', 'spam']:
                    cls._blocked_ids.add(mistral_dict.get('sender_id', None))
                if status_msg == 'seeking_ok':
                    list_msg_dict.append(mistral_dict)
                    logging.info(mistral_dict)
            elif type(mistral_dict) is list:
                # logging.info(f'Mistral: {mistral_dict}')
                for msg_dict in mistral_dict:
                    status_msg = msg_dict.get('category', None)
                    if status_msg in ['scam', 'spam']:
                        cls._blocked_ids.add(msg_dict.get('sender_id', None))
                    if status_msg == 'seeking_ok':
                        logging.info(msg_dict)
                        list_msg_dict.append(msg_dict)
            if list_msg_dict:
                for msg_forward in list_msg_dict:
                    chanel_id_forward = msg_forward.get('chanel_id', None)
                    message_id_forward = msg_forward.get('message_id', None)
                    for msg_obg in _messages_buffer:
                        if (msg_obg.chat_id == chanel_id_forward) and (msg_obg.id == message_id_forward):
                            logging.info(f'Пересылаю сообщение: {msg_obg.to_dict()}')
                            if FORWARD_CHAT_ID:
                                for chat_id in FORWARD_CHAT_ID:
                                    await msg_obg.message.forward_to(chat_id)
                                #await msg_obg.message.forward_to(FORWARD_CHAT_ID)

        except Exception as e:
            logging.info(f'Ошибка Mistral{e}')

    @classmethod
    async def processing_loop(cls) -> None:
        """Фоновая задача, которая периодически вызывает обработку сообщений."""
        while True:
            now = datetime.now(timezone.utc)
            time_since_last = (now - cls._last_processed).total_seconds()

            if time_since_last >= cls._processing_interval:
                await cls._process_buffered_messages()

            await asyncio.sleep(1)
