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


dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """
    This handler receives messages with `/start` command
    """
    # Most event objects have aliases for API methods that can be called in events' context
    # For example if you want to answer to incoming message you can use `message.answer(...)` alias
    # and the target chat will be passed to :ref:`aiogram.methods.send_message.SendMessage`
    # method automatically or call API method directly via
    # Bot instance: `bot.send_message(chat_id=message.chat.id, ...)`
    await message.answer(f"Hello, {message.from_user.full_name}!")


async def main():
    bot = Bot(settings.GET_TOKEN["TOKEN"])
    # like skip_updates=True in earlier versions of aiogram
    await bot.delete_webhook(drop_pending_updates=True)
    dp.include_router(order_router)
    
    # database
    await db.create_tables()

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())