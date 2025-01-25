from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import json


debug_router = Router()

@debug_router.message(F.text == "state")
async def get_state(message: Message, state: FSMContext):
    state_name = await state.get_state()
    if state_name is None:
        await message.answer("Состояние не установлено.")
    else:
        await message.answer(f"Текущее состояние: {state_name}")