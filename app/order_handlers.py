from aiogram import Router, F
from aiogram.types import Message

from app.database import ClientDatabaseHandler

order_router = Router()

ClientHandler = ClientDatabaseHandler()

# Потом красивее оформлю отображение даты
@order_router.message(F.text == "Посмотреть товары")
async def show_products(message: Message):
    # проверка на наличие срока товара
    products = await ClientHandler.get_available_products()
    text = ""
    for product in products:
        text += f"\n\nНазвание товара: {product["name"]}\nОписание товара: {product["description"]}\nЦена товара: {product["price"]}"
        if product["available_until"]:
            text += f"\nДоступен до: {product["available_until"]}"
    await message.answer(text.lstrip("\n\n"))