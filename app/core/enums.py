from enum import StrEnum

from sqlalchemy import Enum as SAEnum


class BillingInterval(StrEnum):
    MONTHLY = "monthly"
    YEARLY = "yearly"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"


class InvoiceStatus(StrEnum):
    DRAFT = "draft"
    ISSUED = "issued"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    VOID = "void"


class PaymentStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"


class LedgerEntryType(StrEnum):
    INVOICE_CREATED = "invoice_created"
    PAYMENT_SUCCESS = "payment_success"
    PAYMENT_FAILURE = "payment_failure"


class LedgerReferenceType(StrEnum):
    INVOICE = "invoice"
    PAYMENT_ATTEMPT = "payment_attempt"


def enum_column(enum_cls: type[StrEnum]) -> SAEnum:
    """Store enums as their string values in a VARCHAR (portable across SQLite/Postgres)."""
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=32,
        values_callable=lambda members: [m.value for m in members],
        validate_strings=True,
    )
