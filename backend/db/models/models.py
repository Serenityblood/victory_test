from datetime import datetime, timezone
from enum import Enum as py_enum

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Text, DateTime, Enum, ForeignKey, String, Integer

from .base import Base
from .mixins import IDMixin, CreatedAtMixin


class Role(py_enum):
    admin = "admin"
    user = "users"
    moderator = "moderator"


class User(Base, IDMixin, CreatedAtMixin):
    name: Mapped[str] = mapped_column(String(128), nullable=True)
    tg_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    # Внести удаление enum поля в downgrade миграции
    role: Mapped[Role] = mapped_column(
        Enum(Role, name="userrole", native_enum=True), nullable=False, default=Role.user
    )
    mailings: Mapped[list["Mailing"]] = relationship(
        back_populates="creator", cascade="all, delete-orphan"
    )


class MailingStatus(py_enum):
    done = "done"
    pending = "pending"


class Mailing(Base, IDMixin, CreatedAtMixin):
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    send_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    extra: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    # Внести удаление enum поля в downgrade миграции
    status: Mapped[MailingStatus] = mapped_column(
        Enum(MailingStatus, name="mailingstatus", native_enum=True),
        default=MailingStatus.pending,
        nullable=False,
    )
    creator_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    # отношение "многие-к-одному": у рассылки есть один создатель
    creator: Mapped["User"] = relationship(back_populates="mailings")
