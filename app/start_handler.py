from aiogram import Router, F 
from aiogram.filters import CommandStart
from aiogram.types import Message, InputMediaPhoto, FSInputFile, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.database import ClientDatabaseHandler
from app.keyboards import show_products_kb

# Constants for file paths
ICONS_PATH = "app/icons/"
MAIN_ICON = f"{ICONS_PATH}main_icon.jfif"
NEW_CLIENT_ICON = f"{ICONS_PATH}new_client.jfif"
SHOW_CATEGORIES_ICON = f"{ICONS_PATH}main_icon1.jfif"
ERROR_ICON = f"{ICONS_PATH}something_went_wrong.jfif"
PRODUCT_ICON = f"{ICONS_PATH}bonny.jfif"
PAYMENT_ICON = f"{ICONS_PATH}payment.jfif"
SUCCESS_ICON = f"{ICONS_PATH}success.jfif"

start_router = Router()
ClientHandler = ClientDatabaseHandler()

# Определяем состояния для FSM
class RegistrationStates(StatesGroup):
    waiting_for_agreement = State()

@start_router.message(CommandStart())
async def command_start_handler(message: Message, state: FSMContext) -> None:
    """Обработка команды /start. Начало работы/Перезапуск бота."""
    await state.clear()
    await state.set_data({})
    
    # Проверяем, существует ли пользователь в базе
    client_info = await ClientHandler.get_client_info(telegram_id=message.from_user.id)

    if client_info:
        # Если пользователь уже существует
        await message.answer_photo(FSInputFile(MAIN_ICON), caption="Привет 🤍\n\nЗдесь ты можешь быстро закинуть гемчиков(и не только) на свой аккаунт.", reply_markup=show_products_kb)
    else:
        # Если пользователь новый, создаем клавиатуру
        inline_kb_builder = InlineKeyboardBuilder()
        inline_kb_builder.button(text="Хорошо", callback_data="agree")

        await message.answer_photo(photo=FSInputFile(NEW_CLIENT_ICON), caption="Добро пожаловать!\n\nБот будет передавать ваши данные(почту и код для входа) исполнителю и только ему.\nТак же и вы будете получать сообщения от исполнителя/поддержки только через бота.\n\nОтветы на некоторые вопросы по работе сервиса можно найти в FAQ(/faq).\n\nДоброго здравия от славянки 🤍", reply_markup=inline_kb_builder.as_markup())
        await state.set_state(RegistrationStates.waiting_for_agreement)


@start_router.callback_query(RegistrationStates.waiting_for_agreement, F.data == "agree")
async def agree_to_terms(callback_query: CallbackQuery, state: FSMContext):
    """Обработка согласия нового пользователя на регистрацию."""

    # Добавляем нового клиента в базу данных
    await ClientHandler.add_new_client(telegram_id=callback_query.from_user.id)
    
    keyboard_builder = InlineKeyboardBuilder()
    keyboard_builder.button(text="Посмотреть товары", callback_data="show_products")

    await callback_query.message.edit_media(InputMediaPhoto(media=FSInputFile(MAIN_ICON), caption="Вы успешно зарегистрированы в системе как клиент.\n\nЕсли возникнут проблемы с заказом, обращайтесь в поддержку(/help)"), reply_markup=keyboard_builder.as_markup())

    await state.clear()
