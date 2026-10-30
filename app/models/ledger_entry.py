from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.billing import utcnow
from app.core.exceptions import LedgerImmutableError
from app.db import Base
from app.core.enums import LedgerEntryType, LedgerReferenceType, enum_column


class LedgerEntry(Base):
    """Append-only record of every money-relevant event.

    (reference_type, reference_id) points at the row that caused the entry,
    e.g. ("invoice", 12) or ("payment_attempt", 40).
    """

    __tablename__ = "ledger_entries"
    __table_args__ = (Index("ix_ledger_reference", "reference_type", "reference_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id"), index=True, nullable=True)
    entry_type: Mapped[LedgerEntryType] = mapped_column(enum_column(LedgerEntryType))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    reference_type: Mapped[LedgerReferenceType] = mapped_column(enum_column(LedgerReferenceType))
    reference_id: Mapped[int] = mapped_column(Integer)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    customer: Mapped["Customer"] = relationship(back_populates="ledger_entries")  # noqa: F821
    invoice: Mapped["Invoice | None"] = relationship(back_populates="ledger_entries")  # noqa: F821


@event.listens_for(LedgerEntry, "before_update")
def _block_ledger_update(mapper, connection, target: LedgerEntry) -> None:
    raise LedgerImmutableError(f"Ledger entry {target.id} is append-only and cannot be updated")


@event.listens_for(LedgerEntry, "before_delete")
def _block_ledger_delete(mapper, connection, target: LedgerEntry) -> None:
    raise LedgerImmutableError(f"Ledger entry {target.id} is append-only and cannot be deleted")
