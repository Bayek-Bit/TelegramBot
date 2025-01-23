from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from app.database import ClientDatabaseHandler
from app.keyboards import create_categories_keyboard, create_products_keyboard

from datetime import datetime
# Русская локализация для datetime
import locale
locale.setlocale(locale.LC_ALL, "Russian")

order_router = Router()
ClientHandler = ClientDatabaseHandler()


# Определяем состояния для выбора товаров и оформления заказа
class ProductStates(StatesGroup):
    choosing_category = State()
    choosing_products = State()
    confirm_order = State()


@order_router.message(F.text == "Посмотреть товары")
async def show_categories(message: Message, state: FSMContext):
    """Обработка команды 'Посмотреть товары'. Вывод доступных категорий."""
    categories = await ClientHandler.get_categories()

    if not categories:
        await message.answer("К сожалению, сейчас нет доступных категорий.")
        return

    # Создаем клавиатуру с категориями
    keyboard = create_categories_keyboard(categories)

    # Сохраняем категории в состоянии
    await state.update_data(categories={cat["name"]: cat["category_id"] for cat in categories})

    await message.answer("Выберите категорию:", reply_markup=keyboard)
    await state.set_state(ProductStates.choosing_category)


@order_router.callback_query(F.data.startswith("category_"))
async def show_products_in_category(callback_query: CallbackQuery, state: FSMContext):
    """Обработка выбора категории и вывод товаров."""
    category_id = int(callback_query.data.split("_")[1])

    # Получаем товары из выбранной категории
    products = await ClientHandler.get_products_by_category(category_id)

    if not products:
        await callback_query.message.answer("В данной категории нет доступных товаров.")
        await callback_query.answer()
        return

    # Создаем клавиатуру с товарами
    keyboard = create_products_keyboard(products)

    await callback_query.message.answer(f"Товары в категории:", reply_markup=keyboard)
    await state.update_data(selected_products=[])  # Инициализация пустого списка для товаров
    await state.set_state(ProductStates.choosing_products)
    await callback_query.answer()



@order_router.callback_query(F.data.startswith("product_"))
async def handle_product_selection(callback_query: CallbackQuery, state: FSMContext):
    """Обработка выбора товара пользователем."""
    product_id = int(callback_query.data.split("_")[1])

    # Получение текущего списка выбранных товаров
    user_data = await state.get_data()
    selected_products = user_data.get("selected_products", [])
    selected_products.append(product_id)  # Добавляем выбранный товар

    # Сохраняем обновленный список
    await state.update_data(selected_products=selected_products)

    await callback_query.answer("Товар добавлен в корзину!")


@order_router.message(F.text == "Закончить выбор")
async def confirm_order(message: Message, state: FSMContext):
    """Обработка завершения выбора товаров и вывод заказа для подтверждения."""
    user_data = await state.get_data()
    selected_products = user_data.get("selected_products", [])

    if not selected_products:
        await message.answer("Вы не выбрали ни одного товара.")
        return

    # Получение информации о выбранных товарах
    products = await ClientHandler.get_products_by_ids(selected_products)

    # Формируем текст заказа
    text = "Вы выбрали следующие товары:\n"
    total_price = 0
    for product in products:
        text += f"\n- {product['name']} ({product['price']} ₽)"
        total_price += product['price']

    text += f"\n\nИтоговая сумма: {total_price} ₽"
    text += "\n\nПодтвердить заказ?"

    # Клавиатура для подтверждения или отмены заказа
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_order")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_order")]
    ])

    await message.answer(text, reply_markup=keyboard)
    await state.set_state(ProductStates.confirm_order)


@order_router.callback_query(F.data == "confirm_order")
async def finalize_order(callback_query: CallbackQuery, state: FSMContext):
    """Обработка подтверждения заказа."""
    user_data = await state.get_data()
    selected_products = user_data.get("selected_products", [])

    # Создание заказа в базе данных
    order_id = await ClientHandler.create_order(callback_query.from_user.id, selected_products)

    await callback_query.message.answer(f"Ваш заказ №{order_id} успешно оформлен!")
    await state.clear()


@order_router.callback_query(F.data == "cancel_order")
async def cancel_order(callback_query: CallbackQuery, state: FSMContext):
    """Обработка отмены заказа."""
    await callback_query.message.answer("Вы отменили оформление заказа.")
    await state.clear()