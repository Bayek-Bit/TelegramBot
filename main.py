import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InputMediaPhoto, FSInputFile, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder

#debug
from test import debug_router

from config import settings

# database
import app.database as db

# orders
from app.order_handlers import order_router

# keyboards
import app.keyboards as kb

dp = Dispatcher()
ClientHandler = db.ClientDatabaseHandler()

# Определяем состояния для FSM
class RegistrationStates(StatesGroup):
    waiting_for_agreement = State()


@dp.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """Обработка команды /start."""
    # Проверяем, существует ли пользователь в базе
    client_info = await ClientHandler.get_client_info(message.from_user.id)

    # Изображения, которые будут отправлены при ответе
    main_photo = FSInputFile("app\\icons\\main_icon.jfif")
    new_client_photo = FSInputFile("app\\icons\\new_client.jfif")

    if client_info:
        # Если пользователь уже существует
        keyboard_builder = InlineKeyboardBuilder()
        keyboard_builder.button(text="Посмотреть товары", callback_data="show_products")
        await message.answer_photo(main_photo, caption="Привет 🤍\n\nЗдесь ты можешь быстро закинуть гемчиков(и не только) на свой аккаунт.", reply_markup=keyboard_builder.as_markup(resize_keyboard=True))
    else:
        # Если пользователь новый, создаем клавиатуру
        inline_kb_builder = InlineKeyboardBuilder()
        inline_kb_builder.button(text="Хорошо", callback_data="agree")

        await message.answer_photo(photo=new_client_photo, caption="Добро пожаловать!\n\nБот будет передавать ваши данные(почту и код для входа) исполнителю и только ему.\nТак же и вы будете получать сообщения от исполнителя/поддержки только через бота.\n\nОтветы на некоторые вопросы по работе сервиса можно найти в FAQ(/faq).\n\nДоброго здравия от славянки 🤍", reply_markup=inline_kb_builder.as_markup())
        await state.set_state(RegistrationStates.waiting_for_agreement)


@dp.callback_query(RegistrationStates.waiting_for_agreement, F.data == "agree")
async def agree_to_terms(callback_query: CallbackQuery, state: FSMContext):
    """Обработка согласия нового пользователя на регистрацию."""
    main_photo = FSInputFile("app\\icons\\main_icon.jfif")
    
    # Добавляем нового клиента в базу данных
    await ClientHandler.add_new_client(telegram_id=callback_query.message.from_user.id)
    
    await callback_query.message.edit_media(InputMediaPhoto(media=main_photo, caption="Вы успешно зарегистрированы в системе как клиент.\n\nЕсли возникнут проблемы с заказом, обращайтесь в поддержку(/help)"))

    await state.clear()


async def main():
    bot = Bot(settings.GET_TOKEN["TOKEN"])
    # like skip_updates=True in earlier versions of aiogram
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Подключаем маршруты
    dp.include_router(order_router)
    dp.include_router(debug_router)

    # Создаем таблицы
    await db.create_tables()
    
    # Запускаем polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
