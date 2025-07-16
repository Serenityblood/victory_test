import logging

from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from backend.bot.templates import start_command_text, error_text
from backend.bot.utils import make_safe_request


router_v1 = Router()
logger = logging.getLogger("HandlerLogger")


@router_v1.message(CommandStart)
async def start(msg: types.Message):
    output_data = dict()
    if starting_text := msg.text:
        # TODO добавить логику регистрации админов\модеров
        pass
    output_data["name"] = msg.from_user.full_name if msg.from_user.full_name else None
    output_data["user_id"] = msg.from_user.id
    response = await make_safe_request(
        msg.bot.api_accessor.register_new_user, **output_data
    )
    if response.status_code == 409:
        await msg.answer(text=response.json().get("detail", error_text))
        return
    if not response:
        await msg.answer(text=error_text)
        return
    api_data = response.json()
    logger.info(
        f"Зарегистрирован новый пользователь. "
        f"id: {api_data['tg_id']}, "
        f"role: {api_data['role']}, "
        f"name: {api_data['name']}"
    )
    await msg.answer(text=start_command_text)


@router_v1.message(Command("constructor"))
async def get_into_mailing_constructor(msg: types.Message, state: FSMContext):
    pass
