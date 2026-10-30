import calendar
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from app.core.enums import BillingInterval

CENT = Decimal("0.01")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_money(value: Decimal | int | float | str) -> Decimal:
    """Normalise any amount to a 2-decimal Decimal."""
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)


def add_months(d: date, months: int) -> date:
    """Add calendar months, clamping the day (Jan 31 + 1 month -> Feb 28/29)."""
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def period_end_for(start: date, interval: BillingInterval) -> date:
    """Exclusive end of a billing period that starts on `start`."""
    if interval == BillingInterval.YEARLY:
        return add_months(start, 12)
    return add_months(start, 1)
