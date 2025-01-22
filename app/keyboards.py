from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from app.database import ClientDatabaseHandler

ClientHandler = ClientDatabaseHandler()

main_kb = ReplyKeyboardMarkup(
    resize_keyboard=True,
    keyboard=[
        [KeyboardButton(text="Сделать заказ")],
        [KeyboardButton(text="История заказов")]
    ]
)

categories_kb = ReplyKeyboardMarkup(keyboard=[[]], resize_keyboard=True)