import os

MAX_NAME_SIZE = 128
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
ALLOWED_TO_ADMIN_MENU_ROLES = ("admin",)
ALLOWED_TO_MAILING_CONSTRUCTOR_ROLES = (
    "admin",
    "moderator",
)
ALLOWED_MEDIA_TYPES = ("animation", "photo", "video")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1/")
SECRET_KEY = os.getenv("SECRET_KEY", "d3cb099dfcbe5c1f2d0514417928df9a")
REDIS_URL = os.getenv("REDIS_URL_FOR_BOT", "redis://localhost:6379/0")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")
ADMIN_KEY = os.getenv("ADMIN_KEY", "123")
