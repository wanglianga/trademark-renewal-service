from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional
from app.core.config import settings


def calculate_grace_period_end(expiry_date: date) -> date:
    return expiry_date + relativedelta(months=settings.GRACE_PERIOD_MONTHS)


def days_until(target_date: date) -> int:
    return (target_date - date.today()).days


def is_expiring_soon(expiry_date: date, days: int = None) -> bool:
    if days is None:
        days = settings.RENEWAL_REMINDER_DAYS
    remaining = days_until(expiry_date)
    return 0 <= remaining <= days


def is_in_grace_period(expiry_date: date, grace_period_end: date) -> bool:
    today = date.today()
    return expiry_date < today <= grace_period_end


def is_overdue(grace_period_end: date) -> bool:
    return date.today() > grace_period_end


def format_date(d: Optional[date]) -> str:
    if d is None:
        return ""
    return d.strftime("%Y-%m-%d")


def parse_date(s: str) -> Optional[date]:
    if not s:
        return None
    for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"]:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None
