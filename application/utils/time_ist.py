from datetime import datetime
from zoneinfo import ZoneInfo

IST_TIMEZONE = ZoneInfo("Asia/Kolkata")


def get_ist_now() -> datetime:
    """Returns the current timezone-aware datetime in Indian Standard Time (IST)."""
    return datetime.now(IST_TIMEZONE)
