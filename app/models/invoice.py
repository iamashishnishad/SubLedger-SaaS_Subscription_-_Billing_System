from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.billing import utcnow
from app.db import Base
from app.core.enums import InvoiceStatus, enum_column


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("subscription_id", "period_start", name="uq_invoice_subscription_period"),
        CheckConstraint("amount_due > 0", name="ck_invoices_amount_due_positive"),
        CheckConstraint("amount_paid >= 0 AND amount_paid <= amount_due", name="ck_invoices_amount_paid_range"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    subscription_id: Mapped[int] = mapped_column(ForeignKey("subscriptions.id"), index=True)
    # Denormalised from the subscription so customer-level queries don't need a join.
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    # Snapshot of plan.price at generation time; later price changes don't touch it.
    amount_due: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[InvoiceStatus] = mapped_column(enum_column(InvoiceStatus), default=InvoiceStatus.ISSUED)
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    subscription: Mapped["Subscription"] = relationship(back_populates="invoices")  # noqa: F821
    customer: Mapped["Customer"] = relationship(back_populates="invoices")  # noqa: F821
    payment_attempts: Mapped[list["PaymentAttempt"]] = relationship(back_populates="invoice")  # noqa: F821
    ledger_entries: Mapped[list["LedgerEntry"]] = relationship(back_populates="invoice")  # noqa: F821

    @property
    def amount_remaining(self) -> Decimal:
        return self.amount_due - self.amount_paid
