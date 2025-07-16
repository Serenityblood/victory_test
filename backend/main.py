from contextlib import asynccontextmanager
from typing import AsyncIterator

from uvicorn import run
from fastapi import FastAPI

from backend.db import db_manager


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    db_manager.init(
        db_url="postgresql+asyncpg://serenity:qwe12345@localhost:5432/test_db"
    )
    yield
    await db_manager.close()


app = FastAPI(lifespan=lifespan)


if __name__ == "__main__":
    run(app)
