from zoneinfo import ZoneInfo

from pydantic import BaseModel, field_serializer, ConfigDict, field_validator
from typing import Optional, Dict, Any
from datetime import datetime

from backend.config import TIMEZONE, DATETIME_FORMAT


class MailingCreate(BaseModel):
    name: str
    send_at: datetime
    extra: Dict[str, Any] = {}
    message: str
    creator_id: int

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        if not value:
            raise ValueError("Строка не должна быть пустой")
        return value


class MailingUpdate(BaseModel):
    name: Optional[str] = None
    send_at: Optional[datetime] = None
    extra: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class MailingRead(BaseModel):
    id: int
    name: str
    send_at: datetime
    extra: Dict[str, Any]
    message: str
    status: str
    creator_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "send_at")
    def serialize_dt(self, value: datetime, _info):
        return value.astimezone(ZoneInfo(TIMEZONE)).isoformat()
