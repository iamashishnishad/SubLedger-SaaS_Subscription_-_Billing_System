from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.billing import period_end_for, to_money
from app.core.enums import InvoiceStatus, SubscriptionStatus
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models import Invoice
from app.repositories import InvoiceRepository, PlanRepository, SubscriptionRepository
from app.services.ledger_service import LedgerService


class InvoiceService:
    def __init__(
        self,
        db: Session,
        subscription_repo: SubscriptionRepository,
        plan_repo: PlanRepository,
        invoice_repo: InvoiceRepository,
        ledger_service: LedgerService,
    ):
        self.db = db
        self.subscription_repo = subscription_repo
        self.plan_repo = plan_repo
        self.invoice_repo = invoice_repo
        self.ledger_service = ledger_service

    def generate_invoice(
        self,
        subscription_id: int,
        period_start: date | None = None,
        period_end: date | None = None,
    ) -> Invoice:
        # 1-3. Fetch subscription and make sure it is billable.
        subscription = self.subscription_repo.get_for_update(subscription_id)
        if subscription is None:
            raise NotFoundError(f"Subscription {subscription_id} not found")
        if subscription.status != SubscriptionStatus.ACTIVE:
            raise BusinessRuleError(f"Subscription {subscription_id} is not active; cannot generate an invoice")

        # 4. Plan price at this moment becomes the invoice's amount_due (snapshot).
        plan = self.plan_repo.get(subscription.plan_id)
        if plan is None:
            raise NotFoundError(f"Plan {subscription.plan_id} not found")

        # 5. Billing period: explicit if given, otherwise the subscription's next period.
        uses_subscription_period = period_start is None
        if uses_subscription_period:
            period_start = subscription.current_period_start
            period_end = subscription.current_period_end
        if period_start >= period_end:
            raise BusinessRuleError("period_start must be before period_end")

        if self.invoice_repo.get_by_subscription_and_period(subscription.id, period_start) is not None:
            raise ConflictError(
                f"An invoice for subscription {subscription.id} starting {period_start} already exists"
            )

        # 6. Persist invoice.
        invoice = self.invoice_repo.add(
            Invoice(
                subscription_id=subscription.id,
                customer_id=subscription.customer_id,
                amount_due=to_money(plan.price),
                amount_paid=to_money(0),
                currency=plan.currency,
                status=InvoiceStatus.ISSUED,
                period_start=period_start,
                period_end=period_end,
                due_date=period_start + timedelta(days=get_settings().invoice_due_days),
            )
        )

        if uses_subscription_period:
            subscription.current_period_start = period_end
            subscription.current_period_end = period_end_for(period_end, plan.billing_interval)

        # 7. Ledger entry in the same transaction.
        self.ledger_service.record_invoice_created(invoice)
        self.db.commit()
        return invoice

    def get_invoice(self, invoice_id: int) -> Invoice:
        invoice = self.invoice_repo.get(invoice_id)
        if invoice is None:
            raise NotFoundError(f"Invoice {invoice_id} not found")
        return invoice

    def list_invoices(self, **filters) -> list[Invoice]:
        return self.invoice_repo.list_invoices(**filters)
