import re

regex = r"^[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ](?:[а-яё]+|\.))?$"
message_texts = [
    "Иванов Иван",
    "Иванов Иван Иванович",
    "Иванов Иван И.",
    "Иванов",  # Не должно срабатывать
    "Иванов Иван",  # Не должно срабатывать
]

for message in message_texts:
    print(f"'{message}':", re.match(regex, message))
