# На будующее:
#   Константный путь для иконок в конфиг файле
#   Ограничения на количество обращений человека к боту.
#   Пользователь может иметь только 1 активный заказ (?)
#   Очередь заказов для исполнителя

import asyncio
import logging
import sys
from aiogram import Dispatcher

from app.bot import bot

#debug
from test import debug_router

import app.database as db
from app.start_handler import start_router
from app.order_handlers import order_router
from app.executor_handlers import executor_router

dp = Dispatcher()

async def main():
    # like skip_updates=True in earlier versions of aiogram
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Подключаем маршруты
    dp.include_router(start_router)
    dp.include_router(order_router)
    dp.include_router(executor_router)
    dp.include_router(debug_router)

    # Создаем таблицы
    await db.create_tables()
    
    # Запускаем polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
