import json


class JsonUtils:
    @staticmethod
    def text_to_json(text: str) -> dict:
        # проверяем есть ли в тексте "[" и "]" это могут быть начало и конец массива словарей
        if '[' in text and ']' in text:
            # если есть, то копируем содержимое внутри
            text = text[text.find('['):text.rfind(']') + 1]
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {}

        # Удаляем из строки ```json в начале и ``` в конце
        text_dict = text.replace("```json", "").replace("```", "")
        try:
            return json.loads(text_dict)
        except json.JSONDecodeError:
            return {}
