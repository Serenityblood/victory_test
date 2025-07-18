import logging
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage

from api_accessor import ApiAccessor
from config import BOT_TOKEN, API_URL, REDIS_URL
from handlers import router_v1
from utils import get_api_token


async def main_polling():
    bot = Bot(token=BOT_TOKEN)
    bot.api_accessor = ApiAccessor(api_url=API_URL, token=get_api_token())
    dp = Dispatcher(storage=RedisStorage.from_url(REDIS_URL))
    dp.include_router(router_v1)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    asyncio.run(main_polling())
