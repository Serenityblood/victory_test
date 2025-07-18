from contextlib import asynccontextmanager
from typing import AsyncIterator

from uvicorn import run
from fastapi import FastAPI

from backend.db import db_manager
from backend.api.users import user_router
from backend.api.mailing import mailing_router
from config import get_db_link


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    db_manager.init(db_url=get_db_link())
    yield
    await db_manager.close()


app = FastAPI(lifespan=lifespan)
app.include_router(user_router, prefix="/api/v1")
app.include_router(mailing_router, prefix="/api/v1")


if __name__ == "__main__":
    run(app)
