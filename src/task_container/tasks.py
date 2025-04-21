import asyncio
from datetime import datetime, timedelta, timezone

from telethon import TelegramClient, events, errors
from src.database.database import Database
from config import DATABASE_URL, MISTRAL_API_KEY, MISTRAL_API_MODEL
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
        mistral_client = MistralAI(MISTRAL_API_KEY, MISTRAL_API_MODEL)
        db = Database(DATABASE_URL)
        twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
        try:
            # принимаем данные из бд
            chats_db = (await db.get_chats_by_status(status='test'))[:10]
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
