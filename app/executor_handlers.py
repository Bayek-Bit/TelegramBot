# Запрос кода после отправки email

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from asyncio import create_task, sleep
from datetime import datetime

from app.bot import bot

from app.database import ExecutorDatabaseHandler, ClientDatabaseHandler

from app.keyboards import create_payment_keyboard


executor_router = Router()
ClientHandler = ClientDatabaseHandler()
ExecutorHandler = ExecutorDatabaseHandler()

SUCCESS_PAYMENT_PHOTO = FSInputFile("app\\icons\\success.jfif")
ERROR_PHOTO = FSInputFile("app\\icons\\something_went_wrong.jfif")


class ExecutorStates(StatesGroup):
    working = State()
    chatting_with_client = State()
    # for future
    chatting_with_support = State()

async def handle_executor_interaction(
    message: Message, 
    state: FSMContext, 
    order_id: int,
    order_details: dict, 
    payment_amount: float, 
    payment_deadline: datetime, 
    payment_sender: str, 
):
    """Handle interaction with the executor."""
    # Формируем список товаров с их описаниями
    product_list = "\n".join(
        [f"{product["product_name"]}: {product["product_description"]}" for product in order_details["products"]]
    )

    executor_id = await ExecutorHandler.assign_executor_to_order(order_id)

    if not executor_id:
        await bot.send_message(
                chat_id=message.from_user.id,
                text="⏳На данный момент все исполнители заняты. Ваш заказ добавлен в очередь."
        )
        
        # После уловных 10 попыток отменять заказ и просить создать позже.
        while not executor_id:
            await sleep(60) # in seconds. Minute because for now we have only 1 executor.
            executor_id = await ExecutorHandler.assign_executor_to_order(order_id)
        
        await bot.send_message(
                chat_id=message.from_user.id,
                text="✨Исполнитель назначен на ваш заказ."
            )
        return "Assigned"     
    
    # Отправляем сообщение исполнителю
    await bot.send_message(
        chat_id=executor_id,
        reply_markup=create_payment_keyboard(order_id=order_details["order_id"]),
        text=(
            f"Заказ №{order_id} на сумму {payment_amount} руб.\n"
            f"Продукты:\n{product_list}\n"
            f"Оплата от: {payment_sender}\n"
            f"Срок оплаты: {payment_deadline.strftime('%H:%M:%S')}"
        )
    )


@executor_router.callback_query(F.data.startswith("approve_payment_"))
async def approve_payment(callback_query: CallbackQuery, state: FSMContext):
    """Обработка подтверждения оплаты исполнителем."""
    try:
        await state.set_state(ExecutorStates.working)
        
        # Извлекаем номер заказа из callback_data
        order_id = int(callback_query.data.split('_')[-1])

        # id клиента
        client_telegram_id = await ExecutorHandler.get_client_telegram_id_by_order_id(order_id=order_id)

        await state.update_data(order_id=order_id)
        await state.update_data(client_telegram_id=client_telegram_id)

        await bot.send_photo(
            chat_id=client_telegram_id,
            photo=SUCCESS_PAYMENT_PHOTO,
            caption="💚Исполнитель подтвердил оплату вашего заказа.\n\n❗Скоро вам на почту придёт код.\nПожалуйста, отправьте его боту.\nИсполнитель зайдёт на ваш аккаунт и выполнит заказ."
        )

    except Exception as e:
        await callback_query.answer(f"Ошибка: {str(e)}")

@executor_router.callback_query(F.data.startswith("reject_payment_"))
async def reject_payment(callback_query: CallbackQuery, state: FSMContext):
    """Обработка подтверждения оплаты исполнителем."""
    try:
        # Извлекаем номер заказа из callback_data
        order_id = int(callback_query.data.split('_')[-1])
        
        await ClientHandler.cancel_order(order_id=order_id)

        # id клиента
        client_telegram_id = await ExecutorHandler.get_client_telegram_id_by_order_id(order_id=order_id)

        await bot.send_photo(
            chat_id=client_telegram_id,
            photo=ERROR_PHOTO,
            caption="💔Исполнитель отклонил оплату вашего заказа.\n\nПожалуйста, свяжитесь с поддержкой."
        )

    except Exception as e:
        await callback_query.answer(f"Ошибка: {str(e)}")