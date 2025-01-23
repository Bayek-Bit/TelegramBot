import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import ReplyKeyboardBuilder

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

    if client_info:
        # Если пользователь уже существует
        await message.answer("Вы уже зарегистрированы в системе. Добро пожаловать!")
    else:
        # Если пользователь новый, создаем клавиатуру
        keyboard_builder = ReplyKeyboardBuilder()
        keyboard_builder.button(text="Согласен")
        keyboard_builder.button(text="Не согласен")
        keyboard_builder.adjust(2)  # Две кнопки в строке

        await message.answer(
            "Добро пожаловать! Для продолжения использования бота ваша почта и Telegram ID "
            "будут храниться в базе данных. Вы согласны?",
            reply_markup=keyboard_builder.as_markup(resize_keyboard=True),
        )
        # Устанавливаем состояние ожидания согласия
        await state.set_state(RegistrationStates.waiting_for_agreement)


@dp.message(RegistrationStates.waiting_for_agreement, F.text == "Согласен")
async def agree_to_terms(message: Message, state: FSMContext):
    """Обработка согласия нового пользователя на регистрацию."""
    # Добавляем нового клиента в базу данных
    await ClientHandler.add_new_client(message.from_user.id)

    # Создаем клавиатуру для просмотра товаров
    keyboard_builder = ReplyKeyboardBuilder()
    keyboard_builder.button(text="Посмотреть товары")

    await message.answer(
        "Вы успешно зарегистрированы в системе как клиент. Добро пожаловать!",
        reply_markup=keyboard_builder.as_markup(resize_keyboard=True),
    )
    # Сбрасываем состояние
    await state.clear()


@dp.message(RegistrationStates.waiting_for_agreement, F.text == "Не согласен")
async def disagree_to_terms(message: Message, state: FSMContext):
    """Обработка отказа пользователя на регистрацию."""
    await message.answer("Вы не можете использовать бот без согласия на обработку данных.\n\nЕсли передумаете - перезапускайте бота при помощи '/start'")
    # Сбрасываем состояние
    await state.clear()


@dp.message(RegistrationStates.waiting_for_agreement)
async def invalid_input_in_registration(message: Message, state: FSMContext):
    """Обработка некорректного ввода во время регистрации."""
    await message.answer("Пожалуйста, выберите один из предложенных вариантов: Согласен или Не согласен.")


async def main():
    bot = Bot(settings.GET_TOKEN["TOKEN"])
    # like skip_updates=True in earlier versions of aiogram
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Подключаем маршруты
    dp.include_router(order_router)

    # Создаем таблицы и обновляем базу данных
    await db.create_tables()
    
    # Запускаем polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
