from datetime import datetime
from typing import List


class MailingReader:
    def __init__(self, mailing: dict):
        self.mailing = mailing

    def render(self) -> str:
        name = self.mailing.get("name")
        extra = self.mailing.get("extra")

        send_at = self.mailing.get("send_at")
        dt = datetime.fromisoformat(send_at)
        send_at = dt.strftime("%Y-%m-%d %H:%M:%S")

        status = self.mailing.get("status")
        message = self.mailing.get("message")
        text = [
            f"Название: {name}",
            f"Время отправления по МСК: {send_at}",
            f"Статус: {status}",
            f"Сообщение: {message}",
        ]
        self._render_extra(text, extra)
        return "\n".join(text)

    @staticmethod
    def _render_extra(text: list, extra: dict) -> List[str]:
        if keyboard := extra.get("keyboard"):
            buttons = ""
            for button in keyboard:
                buttons += str(button) + "\n"
            text.append(f"\nКнопки: \n{buttons}")
        if media := extra.get("media"):
            text.append(f"Вложения: {media}")
        return text
