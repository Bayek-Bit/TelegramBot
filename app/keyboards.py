from aiogram.utils.keyboard import InlineKeyboardBuilder

def create_categories_keyboard(categories):
    """Создание клавиатуры с категориями."""
    keyboard_builder = InlineKeyboardBuilder()
    for category in categories:
        keyboard_builder.button(
            text=category['name'],
            callback_data=f"category_{category['category_id']}"
        )
    return keyboard_builder.as_markup()

def create_products_keyboard(products):
    """Создание клавиатуры с товарами."""
    keyboard_builder = InlineKeyboardBuilder()
    for product in products:
        keyboard_builder.button(
            text=product['name'],
            callback_data=f"product_{product['product_id']}"
        )
    return keyboard_builder.as_markup()
