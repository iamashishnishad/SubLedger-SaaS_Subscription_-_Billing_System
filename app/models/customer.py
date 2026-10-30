from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.billing import utcnow
from app.db import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    # Stored lower-cased by CustomerService; the unique index is the last line of defence.
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="customer")  # noqa: F821
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="customer")  # noqa: F821
    ledger_entries: Mapped[list["LedgerEntry"]] = relationship(back_populates="customer")  # noqa: F821
