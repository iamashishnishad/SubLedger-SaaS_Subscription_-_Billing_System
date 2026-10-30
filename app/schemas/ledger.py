from datetime import datetime
from decimal import Decimal

from app.core.enums import LedgerEntryType, LedgerReferenceType
from app.schemas.common import ORMModel


class LedgerEntryRead(ORMModel):
    id: int
    customer_id: int
    invoice_id: int | None
    entry_type: LedgerEntryType
    amount: Decimal
    currency: str
    reference_type: LedgerReferenceType
    reference_id: int
    description: str | None
    created_at: datetime
