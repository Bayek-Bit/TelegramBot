# TODO:
# 1. Добавить сводку по заказу после нажатия подтверждения, уверен ли и т.п.
# 2. Добавить больше состояний для контроля пользователя:
# например, во время состояния принятияоплаты пользователь не может пользоваться ботом
# 3. Итоговая сумма прямо в сообщении с выбором товаров

from aiogram import Router, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
    CallbackQuery,
    FSInputFile,
    InputMediaPhoto
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from asyncio import sleep, create_task
from datetime import datetime, timedelta

from app.database import ClientDatabaseHandler, ExecutorDatabaseHandler
from app.keyboards import create_categories_keyboard, create_products_keyboard

# Русская локализация для времени
import locale
locale.setlocale(locale.LC_TIME, "Russian")

order_router = Router()
ClientHandler = ClientDatabaseHandler()
ExecutorHandler = ExecutorDatabaseHandler()


# Определяем состояния для выбора товаров и оформления заказа
class ProductStates(StatesGroup):
    choosing_category = State()
    choosing_products = State()
    confirm_order = State()
    waiting_for_payment = State()


@order_router.callback_query(F.data == "show_products")
async def show_categories(callback_query: CallbackQuery, state: FSMContext):
    """Обработка команды 'Посмотреть товары'. Вывод доступных категорий."""
    show_categories_photo = FSInputFile("app\\icons\\main_icon1.jfif")
    error_photo = FSInputFile("app\\icons\\something_went_wrong.jfif")
    
    categories = await ClientHandler.get_categories()

    if not categories:
        await callback_query.message.edit_caption(InputMediaPhoto(media=error_photo, caption="К сожалению, сейчас нет доступных категорий."))
        await callback_query.answer()
        return

    # Создаем клавиатуру с категориями
    categories_keyboard = create_categories_keyboard(categories)

    # Сохраняем категории в состоянии
    await state.update_data(categories={cat["name"]: cat["category_id"] for cat in categories})

    await callback_query.message.edit_media(InputMediaPhoto(media=show_categories_photo,
                                                            caption="Выберите категорию:"),
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

    # Получаем товары из выбранной категории
    products = await ClientHandler.get_products_by_category(category_id)

    if not products:
        await callback_query.message.answer("В данной категории нет доступных товаров.")
        await callback_query.answer()
        return

    # Фото товаров
    product_photo = FSInputFile("app\\icons\\bonny.jfif")
    
    # Создаем клавиатуру с товарами
    keyboard = create_products_keyboard(products)

    # Добавляем кнопки возврата назад и подтверждения заказа
    combined_keyboard = InlineKeyboardMarkup(inline_keyboard=
        keyboard.inline_keyboard + [
            # Первый ряд, состоящий из 1 кнопки сброса
            [InlineKeyboardButton(text="🔄 Сбросить товары", callback_data="reset_products")],
            # Второй ряд кнопок
            [
                InlineKeyboardButton(text="⬅ Вернуться", callback_data="show_products"),
                InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="confirm_order")
            ]
        ]
    )

    await callback_query.message.edit_media(
            InputMediaPhoto(media=product_photo,
                            caption="Товары в категории.\n\n🍁Важно: проверяйте наличие акции в магазине на своём аккаунте."),
            reply_markup=combined_keyboard
                )

    # Проверяем, есть ли уже список выбранных товаров в состоянии, если нет — инициализируем
    user_data = await state.get_data()
    if "selected_products" not in user_data:
        await state.update_data(selected_products={})

    await state.set_state(ProductStates.choosing_products)
    await callback_query.answer()

# Сброс выбранных клиентом продуктов
@order_router.callback_query(F.data == "reset_products")
async def reset_selected_products(callback_query: CallbackQuery, state: FSMContext):
    """Обработка сброса выбранных товаров."""
    await state.update_data(selected_products={})
    await callback_query.answer("Выбранные товары сброшены.")


@order_router.callback_query(F.data == "confirm_order")
async def finalize_order(callback_query: CallbackQuery, state: FSMContext):
    """Обработка подтверждения заказа."""
    payment_photo = FSInputFile("app\\icons\\payment.jfif")
    
    user_data = await state.get_data()
    if not user_data["selected_products"]:
        await callback_query.answer()
        return 
    selected_products = user_data.get("selected_products", {})

    # Подготовка данных для базы (создаем список ID товаров с учетом их количества)
    product_ids_with_count = []
    for product_id, count in selected_products.items():
        product_ids_with_count.extend([product_id] * count)

    # Создание заказа в базе данных
    order_id = await ClientHandler.create_order(callback_query.from_user.id, product_ids_with_count)
    
    # Сохраняем ID заказа и время истечения оплаты
    payment_deadline = datetime.now() + timedelta(minutes=15)
    await state.update_data(order_id=order_id, payment_deadline=payment_deadline)
    
    # Отправляем реквизиты для оплаты
    text = (
        f"Ваш заказ №{order_id} успешно оформлен🖤\n"
        "Для оплаты переведите сумму на указанные реквизиты:\n"
        "Карта: 1234 5678 9012 3456\n"
        "Получатель: Иван Иванов\n"
        "Банк: ТестБанк\n"
        "После оплаты отправьте сообщение с вашим ФИО (например: Иванов И.И. или Иванов Иван И.).\n\n"
        f"Время для оплаты: до {payment_deadline.strftime('%H:%M:%S')}."
    )
    await callback_query.message.edit_media(InputMediaPhoto(media=payment_photo, caption=text))
    await state.set_state(ProductStates.waiting_for_payment)

    # Запускаем таймер для проверки оплаты
    create_task(check_payment_timeout(order_id, payment_deadline, callback_query, state))


async def check_payment_timeout(order_id: int, payment_deadline: datetime, callback_query: CallbackQuery, state: FSMContext):
    """Функция для проверки оплаты по истечении времени."""
    time_remaining = (payment_deadline - datetime.now()).total_seconds()
    if time_remaining > 0:
        await sleep(time_remaining)

    # Проверяем, было ли заказ оплачен
    payment_status = await ClientHandler.get_order_payment_status(order_id=order_id)
    if payment_status == "waiting_for_payment":
        # Отменяем заказ
        await ClientHandler.cancel_order(order_id=order_id)
        await callback_query.message.answer(
            "Время для оплаты истекло. Ваш заказ был отменён. "
            "Вы можете сделать новый заказ или обратиться в поддержку."
        )
        await state.clear()


@order_router.message(ProductStates.waiting_for_payment, F.text.regexp(r"^[А-ЯЁ][а-яё]+( [А-ЯЁ]\.?){1,2}$"))
async def process_payment_confirmation(message: Message, state: FSMContext):
    """Обработка сообщения клиента с подтверждением оплаты."""
    error_photo = FSInputFile("app\\icons\\something_went_wrong.jfif")
    
    user_data = await state.get_data()
    order_id = user_data.get("order_id")

    if not order_id:
        await message.edit_media(InputMediaPhoto(media=error_photo, caption="Нет активного заказа для подтверждения оплаты."))
        return

    client_name = message.text.strip()
    
    # Отправляем сообщение исполнителю
    executor_id = await ClientHandler.get_available_executor()
    if not executor_id:
        await message.edit_media(InputMediaPhoto(media=error_photo, caption="К сожалению, сейчас нет доступных исполнителей. Попробуйте позже."))
        return

    # Тут часть кода с хендлерами для исполнителя, это я допишу 26.01
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data=f"approve_payment_{order_id}")],
        [InlineKeyboardButton(text="❌ Отклонить оплату", callback_data=f"reject_payment_{order_id}")]
    ])

    # Назначение заказа для проверки оплаты, потом только принимает заказ
    # ДОПИСАТЬ тут всё завтра.
    await message.answer(
        f"Оплата от клиента {client_name} поступила. Проверьте перевод и подтвердите, если всё в порядке.",
        reply_markup=keyboard
    )


@order_router.callback_query(F.data.startswith("approve_payment_"))
async def approve_payment(callback_query: CallbackQuery, state: FSMContext):
    """Обработка подтверждения оплаты исполнителем."""
    success_payment_photo = FSInputFile("app\\icons\\success.jfif")
    
    order_id = int(callback_query.data.split("_")[1])

    # Подтверждаем оплату и назначаем заказ исполнителю
    await ExecutorDatabaseHandler.assign_executor_to_order(order_id=order_id)
    await callback_query.message.edit_media(InputMediaPhoto(media=success_payment_photo, caption="Оплата подтверждена. Заказ назначен исполнителю."))
    await state.clear()


@order_router.callback_query(F.data.startswith("reject_payment_"))
async def reject_payment(callback_query: CallbackQuery, state: FSMContext):
    """Обработка отклонения оплаты исполнителем."""
    error_photo = FSInputFile("app\\icons\something_went_wrong.jfif")
    
    order_id = int(callback_query.data.split("_")[1])

    # Отменяем заказ
    # часть с исполнителем, переписать
    # в заказах есть executor_id, поэтому отправляй сообщение по id.
    await ClientHandler.cancel_order(order_id=order_id)
    await callback_query.message.edit_text(
        "Оплата отклонена. Клиенту отправлено сообщение о необходимости повторного оформления."
    )
    # Сообщение клиенту
    await callback_query.message.edit_media(
        InputMediaPhoto(media=error_photo, caption="К сожалению, оплата была отклонена. Пожалуйста, обратитесь в поддержку или проверьте корректность оплаты и попробуйте ещё раз.")
    )
    await state.clear()