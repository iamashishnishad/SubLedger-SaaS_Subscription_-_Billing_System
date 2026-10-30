from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, DateTime, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.billing import utcnow
from app.db import Base
from app.core.enums import BillingInterval, enum_column


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = (CheckConstraint("price > 0", name="ck_plans_price_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    billing_interval: Mapped[BillingInterval] = mapped_column(
        enum_column(BillingInterval), default=BillingInterval.MONTHLY
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="plan")  # noqa: F821
