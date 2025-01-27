from aiogram import Router, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    FSInputFile,
    InputMediaPhoto
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asyncio import create_task
from datetime import datetime, timedelta
import re
import locale

# Local Modules
from app.database import ClientDatabaseHandler
from app.keyboards import create_categories_keyboard, create_products_keyboard
from app.payment import check_payment_timeout
from app.executor_handlers import handle_executor_interaction

# Set Russian locale for time formatting
try:
    locale.setlocale(locale.LC_TIME, "Russian")
except locale.Error:
    locale.setlocale(locale.LC_TIME, "C")

# Constants for file paths
ICONS_PATH = "app/icons/"
SHOW_CATEGORIES_ICON = f"{ICONS_PATH}main_icon1.jfif"
ERROR_ICON = f"{ICONS_PATH}something_went_wrong.jfif"
PRODUCT_ICON = f"{ICONS_PATH}bonny.jfif"
PAYMENT_ICON = f"{ICONS_PATH}payment.jfif"

order_router = Router()
ClientHandler = ClientDatabaseHandler()

# Define states for product selection and order processing
class ProductStates(StatesGroup):
    choosing_category = State()
    choosing_products = State()
    confirm_order = State()
    waiting_for_payment = State()

async def calculate_total(selected_products):
    """Calculate the total price for selected products."""
    if not selected_products:
        return 0

    product_ids = list(selected_products.keys())
    prices = await ClientHandler.get_products_prices(product_ids)
    return sum(prices[pid] * count for pid, count in selected_products.items())

@order_router.callback_query(F.data == "show_products")
async def show_categories(callback_query: CallbackQuery, state: FSMContext):
    """Handle 'View Products' command. Display available categories."""
    categories = await ClientHandler.get_categories()
    user_data = await state.get_data()
    selected_products = user_data.get("selected_products", {})
    total = await calculate_total(selected_products)

    if not categories:
        await callback_query.message.edit_media(
            InputMediaPhoto(media=FSInputFile(ERROR_ICON), caption="К сожалению, сейчас нет доступных категорий.")
        )
        await callback_query.answer()
        return

    # Create categories keyboard
    categories_keyboard = create_categories_keyboard(categories)

    # Update state with categories and selected products
    await state.update_data({
        "categories": {cat["name"]: cat["category_id"] for cat in categories},
        "selected_products": selected_products
    })

    await callback_query.message.edit_media(
        InputMediaPhoto(
            media=FSInputFile(SHOW_CATEGORIES_ICON),
            caption=f"Выберите категорию.\n\n💎Итого: {total}р."
        ),
        reply_markup=categories_keyboard
    )
    await state.set_state(ProductStates.choosing_category)
    await callback_query.answer()

@order_router.callback_query(ProductStates.choosing_products, F.data.startswith("product_"))
async def handle_product_selection(callback_query: CallbackQuery, state: FSMContext):
    """Handle product selection by the user."""
    product_id = int(callback_query.data.split("_")[1])

    user_data = await state.get_data()
    selected_products = user_data.get("selected_products", {})

    # Increment product count
    selected_products[product_id] = selected_products.get(product_id, 0) + 1

    # Update state with new selected products
    await state.update_data({"selected_products": selected_products})

    # Recalculate total and update the message
    total = await calculate_total(selected_products)

    # Retrieve the keyboard from the current message
    current_keyboard = callback_query.message.reply_markup

    await callback_query.message.edit_media(
        InputMediaPhoto(
            media=FSInputFile(PRODUCT_ICON),
            caption=f"Товары в категории\n\n💎Итого: {total}р."
        ),
        reply_markup=current_keyboard
    )

    await callback_query.answer("Товар добавлен в корзину!")

@order_router.callback_query(ProductStates.choosing_category, F.data.startswith("category_"))
async def show_products_in_category(callback_query: CallbackQuery, state: FSMContext):
    """Handle category selection and display products."""
    category_id = int(callback_query.data.split("_")[1])
    products = await ClientHandler.get_products_by_category(category_id)
    user_data = await state.get_data()
    selected_products = user_data.get("selected_products", {})
    total = await calculate_total(selected_products)

    if not products:
        await callback_query.message.answer("В данной категории нет доступных товаров.")
        await callback_query.answer()
        return

    keyboard = create_products_keyboard(products)
    combined_keyboard = InlineKeyboardMarkup(inline_keyboard=
        keyboard.inline_keyboard + [
            [InlineKeyboardButton(text="🔄 Сбросить товары", callback_data="reset_products")],
            [
                InlineKeyboardButton(text="⬅ Вернуться", callback_data="show_products"),
                InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="confirm_order")
            ]
        ]
    )

    await state.update_data({"selected_products": selected_products})

    await callback_query.message.edit_media(
        InputMediaPhoto(
            media=FSInputFile(PRODUCT_ICON),
            caption=f"Товары в категории\n\n💎Итого: {total}р."
        ),
        reply_markup=combined_keyboard
    )
    await state.set_state(ProductStates.choosing_products)
    await callback_query.answer()

@order_router.callback_query(F.data == "reset_products")
async def reset_selected_products(callback_query: CallbackQuery, state: FSMContext):
    """Reset selected products."""
    await state.update_data({"selected_products": {}})

    # Updating total sum to 0
    await callback_query.message.edit_media(
        InputMediaPhoto(
            media=FSInputFile(PRODUCT_ICON),
            caption=f"Товары в категории\n\n💎Итого: 0р."
        ),
        reply_markup=callback_query.message.reply_markup
    )

@order_router.callback_query(F.data == "confirm_order")
async def finalize_order(callback_query: CallbackQuery, state: FSMContext):
    """Handle order confirmation."""
    user_data = await state.get_data()
    selected_products = user_data.get("selected_products", {})

    if not selected_products:
        await callback_query.answer("Корзина пуста!")
        return

    total = await calculate_total(selected_products)
    order_id = await ClientHandler.create_order(callback_query.from_user.id, list(selected_products.keys()))
    payment_deadline = datetime.now() + timedelta(minutes=15)

    await state.update_data({
        "order_id": order_id,
        "payment_deadline": payment_deadline
    })

    await callback_query.message.edit_media(
        InputMediaPhoto(
            media=FSInputFile(PAYMENT_ICON),
            caption=(
                f"Ваш заказ №{order_id} оформлен. Сумма: {total} руб.\n"
                "Для оплаты переведите указанную ботом сумму на эти реквизиты:\n"
                "Карта: 1234 5678 9012 3456\n"
                "Получатель: Иван Иванов\n"
                "Банк: ТестБанк\n"
                f"Время для оплаты: до {payment_deadline.strftime('%H:%M:%S')}\n"
                "После оплаты укажите Ф.И.О. отправителя. Пример: Иван Иванов И. или Иванов Иван Иванович\n"
                "Ф.И.О. отправителя нужно исполнителю для подтверждения платежа."
            )
        )
    )
    await state.set_state(ProductStates.waiting_for_payment)
    create_task(check_payment_timeout(order_id, payment_deadline, callback_query, state, ClientHandler))

@order_router.message(ProductStates.waiting_for_payment, F.text.regexp(r"^[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ](?:[а-яё]+|\.))?$"))
async def process_payment_confirmation(message: Message, state: FSMContext):
    """Handle payment confirmation."""
    user_data = await state.get_data()
    order_id = user_data.get("order_id")

    if not order_id:
        await state.clear()
        await message.answer("Произошла ошибка. Заказ не найден.\n\nПопробуйте оформить заказ ещё раз или обратитесь в поддержку.")
        return

    # Pass order_id to handle_executor_interaction
    await handle_executor_interaction(message, state, order_id=order_id)

@order_router.message(ProductStates.waiting_for_payment)
async def wrong_payment_confirmation_message(message: Message, state: FSMContext):
    """Handle incorrect payment confirmation format."""
    await message.answer("Пожалуйста, в сообщении укажите только Ф.И.О. по примеру, приведённому в сообщении с реквизитами.")
