# Истечение оплаты заказа автоматически освобождать исполнителя

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime

from app.bot import bot

from app.database import ExecutorDatabaseHandler, ClientDatabaseHandler

from app.keyboards import create_payment_keyboard


executor_router = Router()
ClientHandler = ClientDatabaseHandler()
ExecutorHandler = ExecutorDatabaseHandler()


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
    success_payment_photo = FSInputFile("app\\icons\\success.jfif")
    
    try:
        # Извлекаем номер заказа из callback_data
        order_id = int(callback_query.data.split('_')[-1])
        
        # id клиента
        client_telegram_id = await ExecutorHandler.get_client_telegram_id_by_order_id(order_id=order_id)

        await bot.send_photo(
            chat_id=client_telegram_id,
            photo=success_payment_photo,
            caption="💚Исполнитель подтвердил оплату вашего заказа, ожидайте исполнения.\n\n❗Пожалуйста, не заходите на аккаунт, пока не получите сообщение об исполнении заказа."
            )

    except Exception as e:
        await callback_query.answer(f"Ошибка: {str(e)}")

@executor_router.callback_query(F.data.startswith("reject_payment_"))
async def approve_payment(callback_query: CallbackQuery, state: FSMContext):
    """Обработка подтверждения оплаты исполнителем."""
    success_payment_photo = FSInputFile("app\\icons\\success.jfif")
    
    try:
        # Извлекаем номер заказа из callback_data
        order_id = int(callback_query.data.split('_')[-1])
        
        # id клиента
        client_telegram_id = await ExecutorHandler.get_client_telegram_id_by_order_id(order_id=order_id)

        await bot.send_photo(
            chat_id=client_telegram_id,
            photo=success_payment_photo,
            caption="💔Исполнитель отклонил оплату вашего заказа.\n\nПожалуйста, свяжитесь с поддержкой."
            )

    except Exception as e:
        await callback_query.answer(f"Ошибка: {str(e)}")

    # order_id = int(callback_query.data.split("_")[1])

    # # Подтверждаем оплату и назначаем заказ исполнителю
    # await ExecutorDatabaseHandler.assign_executor_to_order(order_id=order_id)
    # await callback_query.message.edit_media(InputMediaPhoto(media=success_payment_photo, caption="Оплата подтверждена. Заказ назначен исполнителю."))
    # await state.clear()


# @order_router.callback_query(F.data.startswith("reject_payment_"))
# async def reject_payment(callback_query: CallbackQuery, state: FSMContext):
#     """Обработка отклонения оплаты исполнителем."""
#     error_photo = FSInputFile("app\\icons\something_went_wrong.jfif")
    
#     order_id = int(callback_query.data.split("_")[1])

#     # Отменяем заказ
#     # часть с исполнителем, переписать
#     # в заказах есть executor_id, поэтому отправляй сообщение по id.
#     await ClientHandler.cancel_order(order_id=order_id)
#     await callback_query.message.edit_text(
#         "Оплата отклонена. Клиенту отправлено сообщение о необходимости повторного оформления."
#     )
#     # Сообщение клиенту
#     await callback_query.message.edit_media(
#         InputMediaPhoto(media=error_photo, caption="К сожалению, оплата была отклонена. Пожалуйста, обратитесь в поддержку или проверьте корректность оплаты и попробуйте ещё раз.")
#     )
#     await state.clear()