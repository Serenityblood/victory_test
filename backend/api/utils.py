import jwt
from datetime import datetime
from zoneinfo import ZoneInfo

from config import TIMEZONE, SECRET_KEY


def to_utc(dt: datetime) -> datetime:
    """Перевести в UTC (если нет tzinfo, считаем что это наша)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(TIMEZONE))
    return dt.astimezone(ZoneInfo("UTC"))


def to_main_tz(dt: datetime) -> datetime:
    """Перевести из UTC в таймзону из config."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo("UTC"))
    return dt.astimezone(ZoneInfo(TIMEZONE))


def decode_jwt(token: str) -> bool:
    """
    Проверка токена на возможность декодирования(проверка secret_key)
    :param token:
    :return: bool
    """
    try:
        jwt.decode(
            token, SECRET_KEY, algorithms=["HS256"], options={"verify_exp": False}
        )
        return True
    except jwt.PyJWTError:
        return False
