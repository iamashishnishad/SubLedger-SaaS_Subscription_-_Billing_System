from datetime import date

from sqlalchemy.orm import Session

from app.core.billing import period_end_for, utcnow
from app.core.enums import SubscriptionStatus
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models import Subscription
from app.repositories import CustomerRepository, PlanRepository, SubscriptionRepository
from app.schemas.subscription import SubscriptionCreate


class SubscriptionService:
    def __init__(
        self,
        db: Session,
        subscription_repo: SubscriptionRepository,
        customer_repo: CustomerRepository,
        plan_repo: PlanRepository,
    ):
        self.db = db
        self.subscription_repo = subscription_repo
        self.customer_repo = customer_repo
        self.plan_repo = plan_repo

    def create_subscription(self, data: SubscriptionCreate) -> Subscription:
        customer = self.customer_repo.get(data.customer_id)
        if customer is None:
            raise NotFoundError(f"Customer {data.customer_id} not found")

        plan = self.plan_repo.get(data.plan_id)
        if plan is None:
            raise NotFoundError(f"Plan {data.plan_id} not found")
        if not plan.is_active:
            raise BusinessRuleError(f"Plan {plan.id} is inactive; new subscriptions are not allowed")

        if self.subscription_repo.get_active_for_customer_and_plan(customer.id, plan.id) is not None:
            raise ConflictError(f"Customer {customer.id} already has an active subscription to plan {plan.id}")

        start = data.start_date or date.today()
        subscription = self.subscription_repo.add(
            Subscription(
                customer_id=customer.id,
                plan_id=plan.id,
                status=SubscriptionStatus.ACTIVE,
                start_date=start,
                current_period_start=start,
                current_period_end=period_end_for(start, plan.billing_interval),
            )
        )
        self.db.commit()
        return subscription

    def get_subscription(self, subscription_id: int) -> Subscription:
        subscription = self.subscription_repo.get(subscription_id)
        if subscription is None:
            raise NotFoundError(f"Subscription {subscription_id} not found")
        return subscription

    def list_for_customer(self, customer_id: int) -> list[Subscription]:
        if self.customer_repo.get(customer_id) is None:
            raise NotFoundError(f"Customer {customer_id} not found")
        return self.subscription_repo.list_for_customer(customer_id)

    def cancel_subscription(self, subscription_id: int) -> Subscription:
        subscription = self.get_subscription(subscription_id)
        if subscription.status == SubscriptionStatus.CANCELLED:
            raise BusinessRuleError(f"Subscription {subscription_id} is already cancelled")
        subscription.status = SubscriptionStatus.CANCELLED
        subscription.cancelled_at = utcnow()
        self.db.commit()
        return subscription
