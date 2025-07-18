from datetime import datetime, timedelta
from typing import Tuple, Dict, Optional

from config import BOT_TOKEN


class MailingReport:
    """Класс для сбора статистики по рассылкам"""

    DELIVERY_METHOD = "sendMessage"

    def __init__(self, mailing_name: str):
        self._start_time: Optional[datetime] = None
        self._stop_time: Optional[datetime] = None
        self.mailing_name = mailing_name
        self._sent: int = 0
        self._error: int = 0

    def add_sent(self) -> None:
        self._sent += 1

    def add_error(self) -> None:
        self._error += 1

    def prepare_report_text(self) -> str:
        text = (
            f"Отчет по рассылке {self.mailing_name}\n"
            f"Отправлено: {self._sent}\n"
            f"Не отправлено: {self._error}\n"
            f"Рассылка выполнена за: {self.executing_time()}"
        )
        return text

    def prepare_data_to_send(self) -> Tuple[str, Dict]:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {"text": self.prepare_report_text(), "parse_mode": "HTML"}
        return url, data

    def start_timer(self):
        self._start_time = datetime.now()

    def stop_timer(self):
        self._stop_time = datetime.now()

    def executing_time(self) -> timedelta:
        if self._stop_time:
            return self._stop_time - self._start_time
        return datetime.now() - self._start_time
