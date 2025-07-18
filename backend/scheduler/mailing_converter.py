from typing import Tuple, Dict, List

from db.models import Mailing
from config import BOT_TOKEN


class MailingSendConverter:
    """Класс для подготовки данных в API телеграмма"""

    DELIVERY_METHODS = {
        "default": "sendMessage",
        "photo": "sendPhoto",
        "video": "sendVideo",
        "animation": "sendAnimation",
    }

    def prepare_to_send(self, mailing: Mailing) -> Tuple[str, Dict]:
        parsed_extra, delivery_method = self._parse_extra(
            mailing.extra, mailing.message
        )
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/{delivery_method}"
        data = parsed_extra
        return url, data

    def _parse_extra(self, extra: Dict, message: str) -> Tuple[Dict, str]:
        parsed_extra = {"parse_mode": "HTML"}
        if keyboard := extra.get("keyboard"):
            parsed_extra["reply_markup"] = {"inline_keyboard": [keyboard]}
        if media := extra.get("media"):
            media_type = media.get("media_type")
            delivery_method = self.DELIVERY_METHODS.get(media_type)
            parsed_extra[media_type] = media["url"]
            parsed_extra["caption"] = message
        else:
            delivery_method = self.DELIVERY_METHODS["default"]
            parsed_extra["text"] = message
        return parsed_extra, delivery_method
