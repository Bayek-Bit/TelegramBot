from aiogram import Router, F
from aiogram.types import Message

from app.database import ClientDatabaseHandler

from datetime import datetime

# Русская локализация
import locale
locale.setlocale(locale.LC_ALL, "Russian")

order_router = Router()
ClientHandler = ClientDatabaseHandler()

@order_router.message(F.text == "Посмотреть товары")
async def show_products(message: Message):
    """Обработка команды 'Посмотреть товары'. Вывод доступных товаров."""
    products = await ClientHandler.get_available_products()
    
    if not products:
        # Если доступных товаров нет, отправляем соответствующее сообщение
        await message.answer("К сожалению, сейчас нет доступных товаров.")
        return

    text = "Доступные товары:\n"
    for product in products:
        text += f"\nНазвание товара: {product['name']}"
        if product["description"]:
            text += f"\nОписание товара: {product['description']}"
        text += f"\nЦена товара: {product['price']} ₽"
        
        if product["available_until"]:
            # Преобразование строки в объект даты и форматирование
            date_object = datetime.strptime(product["available_until"], "%Y-%m-%d %H:%M:%S")
            formatted_date = date_object.strftime("%d %B %Y")
            text += f"\nДоступен до: {formatted_date}"
        
        text += "\n"  # Разделитель между товарами

    await message.answer(text.strip())
