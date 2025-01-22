import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from config import settings

#database
import app.database as db

#orders
from app.order_handlers import order_router

#keyboards
import app.keyboards as kb


dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:

    await message.answer(f"Hello, {message.from_user.full_name}!", reply_markup=kb.main_kb)


async def main():
    bot = Bot(settings.GET_TOKEN["TOKEN"])
    # like skip_updates=True in earlier versions of aiogram
    await bot.delete_webhook(drop_pending_updates=True)
    dp.include_router(order_router)
    
    # database
    await db.create_tables()
    await db.add_categories_to_db()

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())