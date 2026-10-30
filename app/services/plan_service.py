from sqlalchemy.orm import Session

from app.core.billing import to_money
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.models import Plan
from app.repositories import PlanRepository
from app.schemas.plan import PlanCreate, PlanUpdate


class PlanService:
    def __init__(self, db: Session, plan_repo: PlanRepository):
        self.db = db
        self.plan_repo = plan_repo

    def create_plan(self, data: PlanCreate) -> Plan:
        price = to_money(data.price)
        if price <= 0:
            raise BusinessRuleError("Plan price must be greater than 0")
        plan = self.plan_repo.add(
            Plan(
                name=data.name,
                description=data.description,
                price=price,
                currency=data.currency,
                billing_interval=data.billing_interval,
                is_active=data.is_active,
            )
        )
        self.db.commit()
        return plan

    def get_plan(self, plan_id: int) -> Plan:
        plan = self.plan_repo.get(plan_id)
        if plan is None:
            raise NotFoundError(f"Plan {plan_id} not found")
        return plan

    def list_plans(self, active_only: bool = False, offset: int = 0, limit: int = 100) -> list[Plan]:
        return self.plan_repo.list_plans(active_only=active_only, offset=offset, limit=limit)

    def update_plan(self, plan_id: int, data: PlanUpdate) -> Plan:
        """Price changes only affect invoices generated afterwards (invoices snapshot the price)."""
        plan = self.get_plan(plan_id)
        changes = data.model_dump(exclude_unset=True)
        if "price" in changes:
            changes["price"] = to_money(changes["price"])
            if changes["price"] <= 0:
                raise BusinessRuleError("Plan price must be greater than 0")
        for field, value in changes.items():
            setattr(plan, field, value)
        self.db.commit()
        return plan
