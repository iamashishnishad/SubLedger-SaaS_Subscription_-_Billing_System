from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.core.enums import PaymentStatus
from app.schemas.common import CurrencyCode, ORMModel, PositiveMoney
from app.schemas.invoice import InvoiceRead


class PaymentCreate(BaseModel):
    invoice_id: int
    amount: PositiveMoney
    currency: CurrencyCode
    status: PaymentStatus
    provider_reference: str = Field(min_length=1, max_length=120)
    failure_reason: str | None = Field(default=None, max_length=255)


class PaymentAttemptRead(ORMModel):
    id: int
    invoice_id: int
    amount: Decimal
    currency: str
    status: PaymentStatus
    provider_reference: str
    failure_reason: str | None
    created_at: datetime


class PaymentResult(BaseModel):
    payment_attempt: PaymentAttemptRead
    invoice: InvoiceRead
