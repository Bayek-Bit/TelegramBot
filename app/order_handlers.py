from aiogram import Router, F
from aiogram.types import Message

from app.database import ClientDatabaseHandler

from datetime import datetime

# Русская локализация
import locale
locale.setlocale(locale.LC_ALL, "Russian")

order_router = Router()

ClientHandler = ClientDatabaseHandler()

# Добавление описания товара только если оно есть
@order_router.message(F.text == "Посмотреть товары")
async def show_products(message: Message):
    # проверка на наличие срока товара
    products = await ClientHandler.get_available_products()
    text = ""
    for product in products:
        text += f"\n\nНазвание товара: {product["name"]}\nОписание товара: {product["description"]}\nЦена товара: {product["price"]}"
        if product["available_until"]:
            # из 2025-03-
            date_object = datetime.strptime(product["available_until"], "%Y-%m-%d")
            formatted_date = date_object.strftime("%d %B %Y")
            text += f"\nДоступен до: {formatted_date}"
    await message.answer(text.lstrip("\n\n"))