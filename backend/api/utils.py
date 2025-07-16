from datetime import datetime
from zoneinfo import ZoneInfo

from backend.config import TIMEZONE


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
