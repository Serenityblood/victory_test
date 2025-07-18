from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator

from backend.db.models.models import Role
from backend.api.utils import to_main_tz


class UserCreate(BaseModel):
    name: Optional[str] = None
    tg_id: int
    role: str = "users"

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v is None:
            return v
        allowed_roles = {role.value for role in Role}
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of {allowed_roles}")
        return v


class UserRead(BaseModel):
    id: int
    name: Optional[str]
    tg_id: int
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at")
    def serialize_created_at(self, dt: datetime, _info):
        return to_main_tz(dt).isoformat()


class RoleListResponse(BaseModel):
    roles: List[str]


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        if v is None:
            return v
        allowed_roles = {role.value for role in Role}
        if v not in allowed_roles:
            raise ValueError(f"Role must be one of {allowed_roles}")
        return v
