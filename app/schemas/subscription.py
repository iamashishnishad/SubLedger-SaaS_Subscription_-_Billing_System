from datetime import date, datetime

from pydantic import BaseModel

from app.core.enums import SubscriptionStatus
from app.schemas.common import ORMModel


class SubscriptionCreate(BaseModel):
    customer_id: int
    plan_id: int
    start_date: date | None = None  # defaults to today


class SubscriptionRead(ORMModel):
    id: int
    customer_id: int
    plan_id: int
    status: SubscriptionStatus
    start_date: date
    current_period_start: date
    current_period_end: date
    cancelled_at: datetime | None
    created_at: datetime
