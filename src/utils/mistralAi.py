import asyncio
import os
import json
from pathlib import Path

from dotenv import load_dotenv
from mistralai import Mistral
import json


async def get_count_message(input_text: str) -> int:
    text = input_text.replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(text)
        count = data.get("count_message", 0)
        return count
    except Exception as e:
        print(f'Error as e {e}')
        return 0


class MistralAI:
    """
    Класс для взаимодействия с API Mistral.
    """

    def __init__(self, mistral_api_key: str, model: str):
        self.client = Mistral(api_key=mistral_api_key)
        self.model = model

    async def chat(self, message: str, prompt: str) -> str:
        """
        Выполняет чат с заданным сообщением.
        :param prompt: Промпт для AI
        :param message:  Сообщение для чата.
        :return: Ответ от модели.
        """
        messages = [
            {"role": "user", "content": message},
            {"role": "system", "content": prompt}
        ]
        try:
            response = await self.client.chat.complete_async(model=self.model, messages=messages)
            return response.choices[0].message.content
        except Exception as e:
            return f"Возникла ошибка в запросе к Mistral : {e}"


async def main():
    prompt = """
    Твоя роль разделить сообщения на спам, нецензурные сообщения, рекламу. Ты должен вернуть данные в json формате.
    К каждому типу сообщений напиши количество этих сообщений.
    Основная цель, найти пользователей, которые хотят купить услуги по строительству, которым нужна консультация.
    """
    load_dotenv("../../.env")
    mistral_api_key = os.getenv('MISTRAL_API_KEY')
    mistral_api_model = os.getenv('MISTRAL_MODEL')
    # mistral_chat = MistralAI(mistral_api_key, mistral_api_model)
    input_text = """
    ```json
{
  "messages": [
    {
      "id": 5775251814,
      "name": "Мм",
      "message": "Требуется шаурмист на работу. Ищем активного, чистоплотного и вежливого сотрудника. Приветствуется умение готовить шаурму. Со своей стороны гарантируем хорошие условия труда и своевременную оплату. График с 9:00-21:00 Оплата обсуждается в личных сообщениях адрес в богородск",
      "category": "Рекламные"
    },
    {
      "id": 6400945842,
      "name": "MV61",
      "message": "Будет 2",
      "category": "Обычные"
    },
    {
      "id": 6400945842,
      "name": "MV61",
      "message": "1",
      "category": "Обычные"
    },
    {
      "id": 5921745605,
      "name": "Артем",
      "message": "Сколько надо человек?",
      "category": "Обычные"
    },
    {
      "id": 7606088188,
      "name": "Алексей",
      "message": "Выполняем полный комплекс работ по благоустройству: -планировка участка(вручную и механизированным способом) -монтаж брусчатки -монтаж бордюров -устройство посевного газона с гарантией -устройство рулонного газона -устройство автополива -устройство дренажных систем -устройство септиков и дренажных колодцев -освещение участка -устройство забора(кирпич,профлист,штакетник и т.д.) -устройство навесов -устройство отмостки Опыт более 10 лет Также можем взять срочные работы.Инструмент весь имеется(нивелир,виброплиты,глубинные вибраторы и т.д.) Также можем выполнить работы под ключ (с закупкой материалов) Работы выполняются строго по договору с предварительно согласованной сметой,которая не меняется в течение выполнения работ. Выезд на замер и консультация -бесплатно. Работаем с любыми видами оплат(нал,безнал без НДС) Предоставляем гарантию 3 года",
      "category": "Рекламные"
    },
    {
      "id": 7754045797,
      "name": "Александр",
      "message": "Я могу",
      "category": "Обычные"
    },
    {
      "id": 6400945842,
      "name": "MV61",
      "message": "На завтра",
      "category": "Обычные"
    },
    {
      "id": 7754045797,
      "name": "Александр",
      "message": "Сегодня к 9 вечера?",
      "category": "Обычные"
    },
    {
      "id": 6400945842,
      "name": "MV61",
      "message": "В Опалихе, остановка маяк, к 9, оттуда заберут, разгрузить из машины 2 тонны арматуры, просто скинуть на землю. И доски с мусором собрать по стройке, сложить в кучу.400р,минималка 4 часа, оплата на карту в конце.",
      "category": "Обычные"
    },
    {
      "id": 6089479240,
      "name": "Алексей",
      "message": "ГАРАНТИРОВАННО в СРОК сделаем КАЧЕСТВЕННЫЙ ремонт вашего жилья БЕСПЛАТНО замер БЕСПЛАТНО смета БЕСПЛАТНО консультация как правильно сэкономить на ремонте Пишите в лс за консультацией.",
      "category": "Рекламные"
    }
  ],
  "group": true,
  "count_message": 6
}
```
    """
    await get_count_message(input_text)
    # mistral_text = await mistral_chat.chat(input_text, '')
    # print(mistral_text)


if __name__ == '__main__':
    asyncio.run(main())
