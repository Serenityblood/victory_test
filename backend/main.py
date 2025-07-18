import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from uvicorn import run
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from db import db_manager
from api.users import user_router
from api.mailing import mailing_router
from api.utils import decode_jwt
from scheduler import scheduler, check_and_send_mailings
from config import get_db_link, MAILING_SEARCH_INTERVAL


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    db_manager.init(db_url=get_db_link())
    scheduler.add_job(
        check_and_send_mailings, "interval", seconds=MAILING_SEARCH_INTERVAL
    )
    scheduler.start()
    yield
    await db_manager.close()


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def jwt_auth_middleware(request: Request, call_next):
    # Открытые эндпоинты документации
    if request.url.path in ["/docs", "/openapi.json"]:
        return await call_next(request)

    authorization: str = request.headers.get("Authorization")
    if not authorization:
        return JSONResponse(
            status_code=401,
            content={"detail": "Missing or invalid Authorization header"},
        )

    token = authorization
    access = decode_jwt(token)
    if not access:
        return JSONResponse(status_code=401, content={"detail": "Invalid token"})
    return await call_next(request)


app.include_router(user_router, prefix="/api/v1")
app.include_router(mailing_router, prefix="/api/v1")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# if __name__ == "__main__":
#     run(app)
