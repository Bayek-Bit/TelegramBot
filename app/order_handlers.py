# TODO:
# 1. Добавить больше состояний для контроля пользователя:
# Например, во время состояния принятия оплаты пользователь не может пользоваться ботом.
# 2. Итоговая сумма прямо в сообщении с выбором товаров. Отображается всё время, если клиент выбирает категорию или товар. Изначально равна 0.
# 3. Перенести любое взаимодействие с исполнителем в отдельный файл.

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

# Хендлеры для базы данных
from app.database import ClientDatabaseHandler
# Создание клавиатур
from app.keyboards import create_categories_keyboard, create_products_keyboard
# Оплата
from app.payment import check_payment_timeout
# Общение с исполнителем
from app.executor_handlers import handle_executor_interaction

# Русская локализация для времени
import locale
locale.setlocale(locale.LC_TIME, "Russian")



order_router = Router()
ClientHandler = ClientDatabaseHandler()

# Определяем состояния для выбора товаров и оформления заказа
class ProductStates(StatesGroup):
    choosing_category = State()
    choosing_products = State()
    confirm_order = State()
    waiting_for_payment = State()

async def calculate_total(selected_products):
    """Подсчёт итоговой суммы для всех выбранных товаров."""
    if not selected_products:
        return 0

    product_ids = list(selected_products.keys())
    prices = await ClientHandler.get_products_prices(product_ids)
    return sum(prices[pid] * count for pid, count in selected_products.items())

@order_router.callback_query(F.data == "show_products")
async def show_categories(callback_query: CallbackQuery, state: FSMContext):
    """Обработка команды 'Посмотреть товары'. Вывод доступных категорий."""
    show_categories_photo = FSInputFile("app\\icons\\main_icon1.jfif")
    error_photo = FSInputFile("app\\icons\\something_went_wrong.jfif")
    
    categories = await ClientHandler.get_categories()
    user_data = await state.get_data()
    selected_products = user_data.get("selected_products", {})
    total = await calculate_total(selected_products)

    if not categories:
        await callback_query.message.edit_caption(InputMediaPhoto(media=error_photo, caption="К сожалению, сейчас нет доступных категорий."))
        await callback_query.answer()
        return

    # Создаем клавиатуру с категориями
    categories_keyboard = create_categories_keyboard(categories)

    # Сохраняем категории в состоянии
    await state.update_data(categories={cat["name"]: cat["category_id"] for cat in categories})

    await callback_query.message.edit_media(InputMediaPhoto(media=show_categories_photo,
                                                            caption=f"Выберите категорию.\n\n💎Итого: {total}р."),
                                                            reply_markup=categories_keyboard)
    await state.set_state(ProductStates.choosing_category)
    await callback_query.answer()


@order_router.callback_query(ProductStates.choosing_products, F.data.startswith("product_"))
async def handle_product_selection(callback_query: CallbackQuery, state: FSMContext):
    """Обработка выбора товара пользователем."""
    product_id = int(callback_query.data.split("_")[1])

    # Получение текущего списка выбранных товаров
    user_data = await state.get_data()
    selected_products = user_data.get("selected_products", {})  # Убедитесь, что это словарь

    # Увеличиваем количество товара, если он уже был выбран
    selected_products[product_id] = selected_products.get(product_id, 0) + 1

    # Сохраняем обновленный список
    await state.update_data(selected_products=selected_products)

    await callback_query.answer("Товар добавлен в корзину!")

# @order_router.message(F.text == "reset_state")
# async def reset_state(message: Message, state: FSMContext):
#     await state.clear()
#     await message.answer("Cancelled", reply_markup=ReplyKeyboardRemove())

@order_router.callback_query(ProductStates.choosing_category, F.data.startswith("category_"))
async def show_products_in_category(callback_query: CallbackQuery, state: FSMContext):
    """Обработка выбора категории и вывод товаров."""
    category_id = int(callback_query.data.split("_")[1])
    products = await ClientHandler.get_products_by_category(category_id)
    user_data = await state.get_data()
    selected_products = user_data.get("selected_products", {})
    total = await calculate_total(selected_products)

    if not products:
        await callback_query.message.answer("В данной категории нет доступных товаров.")
        await callback_query.answer()
        return

    product_photo = FSInputFile("app\\icons\\bonny.jfif")
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

    await callback_query.message.edit_media(
        InputMediaPhoto(media=product_photo, caption=f"Товары в категории\n\n💎Итого: {total}р."),
        reply_markup=combined_keyboard
    )
    if "selected_products" not in user_data:
        await state.update_data(selected_products={})

    await state.set_state(ProductStates.choosing_products)
    await callback_query.answer()

@order_router.callback_query(F.data == "reset_products")
async def reset_selected_products(callback_query: CallbackQuery, state: FSMContext):
    """Сброс выбранных товаров."""
    await state.update_data(selected_products={})
    await callback_query.answer("Выбранные товары сброшены.")


@order_router.callback_query(F.data == "confirm_order")
async def finalize_order(callback_query: CallbackQuery, state: FSMContext):
    """Обработка подтверждения заказа."""
    payment_photo = FSInputFile("app\\icons\\payment.jfif")
    user_data = await state.get_data()
    selected_products = user_data.get("selected_products", {})
    
    if not selected_products:
        await callback_query.answer("Корзина пуста!")
        return
    
    total = await calculate_total(selected_products)
    order_id = await ClientHandler.create_order(callback_query.from_user.id, list(selected_products.keys()))
    payment_deadline = datetime.now() + timedelta(minutes=15)
    
    await state.update_data(order_id=order_id, payment_deadline=payment_deadline)
    await callback_query.message.edit_media(
        InputMediaPhoto(media=payment_photo, caption=(
            f"Ваш заказ №{order_id} оформлен. Сумма: {total} руб.\n"
            "Для оплаты переведите указанную ботом сумму на эти реквизиты:\n"
            "Карта: 1234 5678 9012 3456\n"
            "Получатель: Иван Иванов\n"
            "Банк: ТестБанк\n"
            f"Время для оплаты: до {payment_deadline.strftime('%H:%M:%S')}\n"
            "После оплаты укажите Ф.И.О. отправителя. Пример: Иван Иванов И. или.\n"
            "Ф.И.О. отправителя нужно исполнителю для подтверждения платежа."
        ))
    )
    await state.set_state(ProductStates.waiting_for_payment)
    create_task(check_payment_timeout(order_id, payment_deadline, callback_query, state, ClientHandler))

@order_router.message(ProductStates.waiting_for_payment, F.text.regexp(r"^[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ](?:[а-яё]+|\.))?$"))
async def process_payment_confirmation(message: Message, state: FSMContext):
    """Обработка подтверждения оплаты."""
    await handle_executor_interaction(message, state)

@order_router.message(ProductStates.waiting_for_payment)
async def wrong_payment_confirmation_message(message: Message, state: FSMContext):
    """Обработка неверного указания Ф.И.О. клиентом"""
    await message.answer("Пожалуйста, в сообщении укажите только Ф.И.О. по примеру, приведённому в сообщении с реквизитами.")