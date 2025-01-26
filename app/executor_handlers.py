from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State


executor_router = Router()


async def handle_executor_interaction(message, state):
    pass

# @order_router.message(ProductStates.waiting_for_payment, F.text.regexp(r"^[А-ЯЁ][а-яё]+( [А-ЯЁ]\.?){1,2}$"))
# async def process_payment_confirmation(message: Message, state: FSMContext):
#     """Обработка сообщения клиента с подтверждением оплаты."""
#     error_photo = FSInputFile("app\\icons\\something_went_wrong.jfif")
    
#     user_data = await state.get_data()
#     order_id = user_data.get("order_id")

#     if not order_id:
#         await message.edit_media(InputMediaPhoto(media=error_photo, caption="Нет активного заказа для подтверждения оплаты."))
#         return

#     client_name = message.text.strip()
    
#     # Отправляем сообщение исполнителю
#     executor_id = await ClientHandler.get_available_executor()
#     if not executor_id:
#         await message.edit_media(InputMediaPhoto(media=error_photo, caption="К сожалению, сейчас нет доступных исполнителей. Попробуйте позже."))
#         return

#     # Тут часть кода с хендлерами для исполнителя, это я допишу 26.01
#     keyboard = InlineKeyboardMarkup(inline_keyboard=[
#         [InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data=f"approve_payment_{order_id}")],
#         [InlineKeyboardButton(text="❌ Отклонить оплату", callback_data=f"reject_payment_{order_id}")]
#     ])

#     # Назначение заказа для проверки оплаты, потом только принимает заказ
#     # ДОПИСАТЬ тут всё завтра.
#     await message.answer(
#         f"Оплата от клиента {client_name} поступила. Проверьте перевод и подтвердите, если всё в порядке.",
#         reply_markup=keyboard
#     )


# @order_router.callback_query(F.data.startswith("approve_payment_"))
# async def approve_payment(callback_query: CallbackQuery, state: FSMContext):
#     """Обработка подтверждения оплаты исполнителем."""
#     success_payment_photo = FSInputFile("app\\icons\\success.jfif")
    
#     order_id = int(callback_query.data.split("_")[1])

#     # Подтверждаем оплату и назначаем заказ исполнителю
#     await ExecutorDatabaseHandler.assign_executor_to_order(order_id=order_id)
#     await callback_query.message.edit_media(InputMediaPhoto(media=success_payment_photo, caption="Оплата подтверждена. Заказ назначен исполнителю."))
#     await state.clear()


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