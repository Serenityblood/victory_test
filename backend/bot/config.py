import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1/")
SECRET_KEY = os.getenv("SECRET_KEY", "d3cb099dfcbe5c1f2d0514417928df9a")
REDIS_URL = os.getenv("REDIS_URL_FOR_BOT", "redis://localhost:6379/0")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")
