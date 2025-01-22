from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.database import ClientDatabaseHandler

from datetime import datetime
# Русская локализация для datetime
import locale
locale.setlocale(locale.LC_ALL, "Russian")

order_router = Router()
ClientHandler = ClientDatabaseHandler()

# Определяем состояние для выбора категории
class ProductStates(StatesGroup):
    choosing_category = State()


@order_router.message(F.text == "Посмотреть товары")
async def show_categories(message: Message, state: FSMContext):
    """Обработка команды 'Посмотреть товары'. Вывод доступных категорий."""
    categories = await ClientHandler.get_categories()

    if not categories:
        await message.answer("К сожалению, сейчас нет доступных категорий.")
        return

    # Формируем кнопки с категориями
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for category in categories:
        keyboard.add(KeyboardButton(category["name"]))

    # Сохраняем категории в состояние
    await state.update_data(categories={cat["name"]: cat["category_id"] for cat in categories})

    await message.answer("Выберите категорию:", reply_markup=keyboard)
    await state.set_state(ProductStates.choosing_category)


@order_router.message(ProductStates.choosing_category)
async def show_products_in_category(message: Message, state: FSMContext):
    """Обработка выбора категории и вывод товаров."""
    user_data = await state.get_data()
    categories = user_data.get("categories", {})

    # Получаем ID выбранной категории
    category_name = message.text
    category_id = categories.get(category_name)

    if not category_id:
        await message.answer("Пожалуйста, выберите категорию из предложенного списка.")
        return

    # Получаем товары из выбранной категории
    products = await ClientHandler.get_products_by_category(category_id)

    if not products:
        await message.answer(f"В категории '{category_name}' нет доступных товаров.")
        return

    # Формируем сообщение с товарами
    text = f"Товары в категории '{category_name}':\n"
    for product in products:
        text += f"\nНазвание товара: {product['name']}"
        if product["description"]:
            text += f"\nОписание товара: {product['description']}"
        text += f"\nЦена товара: {product['price']} ₽"
        
        if product["available_until"]:
            date_object = datetime.strptime(product["available_until"], "%Y-%m-%d %H:%M:%S")
            formatted_date = date_object.strftime("%d %B %Y")
            text += f"\nДоступен до: {formatted_date}"
        
        text += "\n"  # Разделитель между товарами

    await message.answer(text.strip())

    # Завершаем состояние
    await state.clear()