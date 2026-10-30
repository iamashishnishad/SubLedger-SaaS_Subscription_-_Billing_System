from datetime import datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.billing import utcnow
from app.db import Base
from app.core.enums import PaymentStatus, enum_column


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"
    __table_args__ = (CheckConstraint("amount > 0", name="ck_payment_attempts_amount_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[PaymentStatus] = mapped_column(enum_column(PaymentStatus))
    # The gateway's id for this attempt. Unique so a retried webhook can't be counted twice.
    provider_reference: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    invoice: Mapped["Invoice"] = relationship(back_populates="payment_attempts")  # noqa: F821
