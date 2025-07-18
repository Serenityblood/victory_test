from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Optional

from aiogram import types

from config import MAX_NAME_SIZE, DATETIME_FORMAT, TIMEZONE


class NameValidationError(Exception):
    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return self.message


class SendAtValidationError(Exception):
    def __init__(self, message: str):
        self.message = message

    def __str__(self):
        return self.message


class MailingConstructor:
    MAX_NAME_SIZE: int = MAX_NAME_SIZE
    DATETIME_FORMAT: str = DATETIME_FORMAT

    def __init__(
        self,
        name: str,
        message: str,
        creator_id: int,
        send_at: Optional[str] = None,
        keyboard=None,
        media=None,
    ):
        if media is None:
            media = {}
        if keyboard is None:
            keyboard = []
        self._creator_id = creator_id
        self._name = name
        self._message = message
        self._keyboard = keyboard
        self._media = media
        self._send_at = send_at

    def to_dict(self):
        return {
            "name": self._name,
            "message": self._message,
            "creator_id": self._creator_id,
            "send_at": self._send_at,
            "extra": {"keyboard": self._keyboard, "media": self._media}
        }

    @classmethod
    def from_dict(cls, d: dict):
        return cls(name=d["name"], message=d["message"], creator_id=d["creator_id"], send_at=d["send_at"], keyboard=d["extra"].get("keyboard", []), media=d["extra"].get("media", {}))

    def add_button(self, text, url) -> None:
        self._keyboard.append({"text": text, "url": url})

    def delete_button(self, index) -> None:
        self._keyboard.pop(index)

    def replace_button(self, index: int, text: str, url: str) -> None:
        self._keyboard[index] = {"text": text, "url": url}

    def add_media(self, media_type, url) -> None:
        self._media = {"media_type": media_type, "url": url}

    def delete_media(self) -> None:
        self._media = []

    def change_name(self, name: str) -> None:
        if not self.validate_name(name):
            raise NameValidationError("Слишком большая длинна названия")
        self._name = name

    def change_message(self, message: str) -> None:
        self._message = message

    def send_now(self):
        self._send_at = None

    def change_send_at(self, send_at: str) -> None:
        if not self.validate_send_at(send_at):
            raise SendAtValidationError(
                f"Неправильный формат даты. Нужен {self.DATETIME_FORMAT}. Или указано время до нынешнего момента."
            )
        self._send_at = self.convert_datestring_to_correct_format(send_at)

    def to_db(self) -> Dict:
        data = {
            "name": self._name,
            "message": self._message,
            "creator_id": self._creator_id,
        }
        if self._send_at:
            data.update({"send_at": self._send_at})
        extra = dict()
        if self.has_keyboard:
            extra.update({"keyboard": self._keyboard})
        if self.has_media:
            extra.update({"media": self._media})
        if extra:
            data.update({"extra": extra})
        return data

    def represent(self) -> str:
        text = (
            f"Название: {self._name}\n"
            f"Сообщение:\n{self._message}\n\n"
            f"Время отправки МСК: {self._send_at if self._send_at else "сейчас"}\n"
        )
        if self.has_keyboard:
            text += f"Кнопки: \n{'\n'.join([str(b) for b in self._keyboard])}\n\n"
        if self.has_media:
            text += f"Медиа: {self._media}"
        return text

    @staticmethod
    def parse_media_url(msg: types.Message, media_type: str) -> Optional[str]:
        try:
            content = getattr(msg, media_type)
            if media_type == "photo" and type(content) is list:
                size_count = len(content)
                url = content[size_count-1].file_id
            else:
                url = content.file_id
        except AttributeError:
            url = msg.text
        return url

    @classmethod
    def validate_name(cls, s: str) -> bool:
        return len(s.encode("utf-8")) <= cls.MAX_NAME_SIZE

    @classmethod
    def validate_send_at(cls, s: str) -> bool:
        try:
            dt = datetime.strptime(s, cls.DATETIME_FORMAT)
            dt = dt.replace(tzinfo=ZoneInfo(TIMEZONE))
            if datetime.now(ZoneInfo(TIMEZONE)) > dt:
                return False
            return True
        except ValueError:
            return False

    @staticmethod
    def convert_datestring_to_correct_format(datestring):
        return datetime.strptime(datestring, DATETIME_FORMAT).strftime(DATETIME_FORMAT)

    @property
    def has_keyboard(self):
        return True if self._keyboard else False

    @property
    def has_media(self):
        return True if self._media else False
