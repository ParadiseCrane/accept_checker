"""Contains date and time management class"""
from datetime import datetime
import pytz


class DateTimeInfo:
    """Contains date and time information"""

    def __init__(self, timezone_region: str = "Europe/Moscow") -> None:
        self.timezone_region = timezone_region
        self.tz = pytz.timezone(self.timezone_region)  # pylint: disable=C0103

    def get_datetime_now(self) -> datetime:
        """Returns datetime.now() with timezone

        Returns:
            datetime: datetime.now() with timezone
        """
        return datetime.now(tz=self.tz)

    def get_datetime_now_formatted(self, format_string: str) -> str:
        """Returns datetime.now().strftime(...) with timezone

        Returns:
            datetime: datetime.now().strftime(...) with timezone
        """
        return datetime.now(tz=self.tz).strftime(format_string)


DATE_TIME_INFO = DateTimeInfo()
