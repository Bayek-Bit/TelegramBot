from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from datetime import datetime

from asyncio import sleep

from app.database import ClientDatabaseHandler, ExecutorDatabaseHandler

# Пока что инициализирую здесь, надо подумать над местом, где лучше расположить функцию
ExecutorHandler = ExecutorDatabaseHandler()

async def check_payment_timeout(
        order_id: int,
        payment_deadline: datetime,
        message: Message,
        state: FSMContext,
        ClientHandler: ClientDatabaseHandler
    ):
    """Функция для проверки оплаты по истечении времени."""
    time_remaining = (payment_deadline - datetime.now()).total_seconds()
    if time_remaining > 0:
        await sleep(time_remaining)

    # Проверяем, было ли заказ оплачен
    payment_status = await ClientHandler.get_order_payment_status(order_id=order_id)
    if payment_status == "waiting_for_payment":
        # Отменяем заказ
        await ClientHandler.cancel_order(order_id=order_id)
        await message.answer(
            "Время для оплаты истекло. Ваш заказ был отменён. "
            "Вы можете сделать новый заказ или обратиться в поддержку."
        )
        await state.clear()