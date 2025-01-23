import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from config import settings

#database
import app.database as db

#orders
from app.order_handlers import order_router

#keyboards
import app.keyboards as kb


dp = Dispatcher()

ClientHandler = db.ClientDatabaseHandler()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """Обработка команды /start."""
    # Проверяем, существует ли пользователь в базе
    client_info = await ClientHandler.get_client_info(message.from_user.id)

    if client_info:
        # Если пользователь уже существует
        await message.answer("Вы уже зарегистрированы в системе. Добро пожаловать!")
    else:
        # Если пользователь новый
        keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
        keyboard.add(KeyboardButton("Согласен"), KeyboardButton("Не согласен"))

        await message.answer(
            "Добро пожаловать! Для продолжения использования бота ваша почта и Telegram ID "
            "будут храниться в базе данных. Вы согласны?",
            reply_markup=keyboard,
        )

@dp.message(F.text == "Согласен")
async def agree_to_terms(message: Message):
    """Обработка согласия нового пользователя на регистрацию."""
    # Добавляем нового клиента в базу данных
    await ClientHandler.add_new_client(message.from_user.id)
    await message.answer(
        "Вы успешно зарегистрированы в системе как клиент. Добро пожаловать!",
        reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(
            KeyboardButton("Посмотреть товары")
        ),
    )

@dp.message(F.text == "Не согласен")
async def disagree_to_terms(message: Message):
    """Обработка отказа пользователя на регистрацию."""
    await message.answer("Вы не можете использовать бот без согласия на обработку данных.")


async def main():
    bot = Bot(settings.GET_TOKEN["TOKEN"])
    # like skip_updates=True in earlier versions of aiogram
    await bot.delete_webhook(drop_pending_updates=True)
    dp.include_router(order_router)
    
    # database
    await db.create_tables()
    #await db.add_categories_to_db()

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())