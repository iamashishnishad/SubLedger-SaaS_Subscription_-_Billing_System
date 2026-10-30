from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.billing import utcnow
from app.db import Base
from app.core.enums import SubscriptionStatus, enum_column


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        # At most one ACTIVE subscription per (customer, plan). Cancelled rows are
        # ignored by the partial index, so a customer can re-subscribe later.
        Index(
            "uq_active_subscription_per_plan",
            "customer_id",
            "plan_id",
            unique=True,
            sqlite_where=text("status = 'active'"),
            postgresql_where=text("status = 'active'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), index=True)
    status: Mapped[SubscriptionStatus] = mapped_column(
        enum_column(SubscriptionStatus), default=SubscriptionStatus.ACTIVE
    )
    start_date: Mapped[date] = mapped_column(Date)
    # The next period to be invoiced: [current_period_start, current_period_end).
    current_period_start: Mapped[date] = mapped_column(Date)
    current_period_end: Mapped[date] = mapped_column(Date)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    customer: Mapped["Customer"] = relationship(back_populates="subscriptions")  # noqa: F821
    plan: Mapped["Plan"] = relationship(back_populates="subscriptions")  # noqa: F821
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="subscription")  # noqa: F821
