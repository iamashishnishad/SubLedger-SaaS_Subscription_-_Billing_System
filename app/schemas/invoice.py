from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, model_validator

from app.core.enums import InvoiceStatus
from app.schemas.common import ORMModel


class InvoiceGenerate(BaseModel):
    subscription_id: int
    # Optional explicit billing period. Omit both to bill the subscription's next period.
    period_start: date | None = None
    period_end: date | None = None

    @model_validator(mode="after")
    def check_period(self) -> "InvoiceGenerate":
        if (self.period_start is None) != (self.period_end is None):
            raise ValueError("period_start and period_end must be provided together")
        if self.period_start and self.period_end and self.period_start >= self.period_end:
            raise ValueError("period_start must be before period_end")
        return self


class InvoiceRead(ORMModel):
    id: int
    subscription_id: int
    customer_id: int
    amount_due: Decimal
    amount_paid: Decimal
    amount_remaining: Decimal
    currency: str
    status: InvoiceStatus
    period_start: date
    period_end: date
    due_date: date
    created_at: datetime
    updated_at: datetime
