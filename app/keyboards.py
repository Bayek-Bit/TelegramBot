from aiogram.utils.keyboard import InlineKeyboardBuilder

show_products_kb = InlineKeyboardBuilder()
show_products_kb.button(text="Посмотреть товары", callback_data="show_products")
show_products_kb = show_products_kb.as_markup()

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

def create_payment_keyboard(order_id: int):
    """Создание клавиатуры с подтверждением оплаты"""
    payment_kb = InlineKeyboardBuilder()
    payment_kb.button(text="💚Подтвердить оплату", callback_data=f"approve_payment_{order_id}")
    payment_kb.button(text="⛔Отклонить оплату", callback_data=f"reject_payment_{order_id}")
    payment_kb.adjust(1)
    return payment_kb.as_markup()

def create_finish_order_keyboard():
    """Создание клавиатуры для подтверждения выполнения заказа"""
    finish_order_kb = InlineKeyboardBuilder()
    finish_order_kb.button(text="✅Заказ выполнен", callback_data="complete_order")
    return finish_order_kb.as_markup()

show_menu_kb = InlineKeyboardBuilder()
show_menu_kb.button(text="🏠 Главная", callback_data="home")
show_menu_kb = show_menu_kb.as_markup()