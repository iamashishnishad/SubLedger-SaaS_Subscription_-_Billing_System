from sqlalchemy import select

from app.core.enums import SubscriptionStatus
from app.models import Subscription
from app.repositories.base import BaseRepository


class SubscriptionRepository(BaseRepository[Subscription]):
    model = Subscription

    def get_for_update(self, subscription_id: int) -> Subscription | None:
        # Row lock on Postgres so two concurrent invoice runs can't bill the same period.
        stmt = select(Subscription).where(Subscription.id == subscription_id).with_for_update()
        return self.session.scalar(stmt)

    def get_active_for_customer_and_plan(self, customer_id: int, plan_id: int) -> Subscription | None:
        stmt = select(Subscription).where(
            Subscription.customer_id == customer_id,
            Subscription.plan_id == plan_id,
            Subscription.status == SubscriptionStatus.ACTIVE,
        )
        return self.session.scalar(stmt)

    def list_for_customer(self, customer_id: int) -> list[Subscription]:
        stmt = select(Subscription).where(Subscription.customer_id == customer_id).order_by(Subscription.id)
        return list(self.session.scalars(stmt))
