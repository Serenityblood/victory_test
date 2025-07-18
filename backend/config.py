import os

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
MAX_NAME_SIZE = 128
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DB_DRIVER = os.getenv("DB_DRIVER", "postgresql+asyncpg")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_USER = os.getenv("POSTGRES_USER", "serenity")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "12345")
DB_NAME = os.getenv("DB_NAME", "test_db")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
REDIS_URL = os.getenv("REDIS_URL_FOR_CELERY", "redis://localhost:6379/1")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")
SECRET_KEY = os.getenv("SECRET_KEY", "d3cb099dfcbe5c1f2d0514417928df9a")


def get_db_link() -> str:
    return f"{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
