from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.core.enums import BillingInterval
from app.schemas.common import CurrencyCode, ORMModel, PositiveMoney


class PlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    price: PositiveMoney
    currency: CurrencyCode = "INR"
    billing_interval: BillingInterval = BillingInterval.MONTHLY
    is_active: bool = True


class PlanUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    price: PositiveMoney | None = None
    is_active: bool | None = None


class PlanRead(ORMModel):
    id: int
    name: str
    description: str | None
    price: Decimal
    currency: str
    billing_interval: BillingInterval
    is_active: bool
    created_at: datetime
    updated_at: datetime
