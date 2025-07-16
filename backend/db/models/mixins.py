from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column


class IDMixin:
    id: Mapped[Integer] = mapped_column(Integer, primary_key=True)
