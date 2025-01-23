# from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def create_categories_keyboard(categories):
    """Создание клавиатуры с категориями."""
    keyboard = InlineKeyboardMarkup()
    for category in categories:
        keyboard.add(InlineKeyboardButton(text=category['name'], callback_data=f"category_{category['id']}"))
    return keyboard

def create_products_keyboard(products):
    """Создание клавиатуры с товарами."""
    keyboard = InlineKeyboardMarkup()
    for product in products:
        keyboard.add(InlineKeyboardButton(text=product['name'], callback_data=f"product_{product['id']}"))
    return keyboard
