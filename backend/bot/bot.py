import asyncio

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from backend.bot.api_accessor import ApiAccessor
from backend.bot.config import BOT_TOKEN, API_URL, REDIS_URL
from backend.bot.handlers import router_v1
from backend.bot.utils import get_api_token


async def main_polling():
    bot = Bot(token=BOT_TOKEN)
    bot.api_accessor = ApiAccessor(api_url=API_URL, token=get_api_token())
    dp = Dispatcher(storage=RedisStorage.from_url(REDIS_URL))
    dp.include_router(router_v1)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main_polling())
