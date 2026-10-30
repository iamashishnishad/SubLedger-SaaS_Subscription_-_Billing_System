from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.billing import to_money
from app.core.enums import InvoiceStatus, PaymentStatus
from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models import Invoice, PaymentAttempt
from app.repositories import InvoiceRepository, PaymentAttemptRepository
from app.services.ledger_service import LedgerService

PAYABLE_STATUSES = {InvoiceStatus.ISSUED, InvoiceStatus.PARTIALLY_PAID}


class PaymentService:
    def __init__(
        self,
        db: Session,
        invoice_repo: InvoiceRepository,
        payment_attempt_repo: PaymentAttemptRepository,
        ledger_service: LedgerService,
    ):
        self.db = db
        self.invoice_repo = invoice_repo
        self.payment_attempt_repo = payment_attempt_repo
        self.ledger_service = ledger_service

    def record_payment(
        self,
        invoice_id: int,
        amount: Decimal,
        currency: str,
        status: PaymentStatus,
        provider_reference: str,
        failure_reason: str | None = None,
    ) -> tuple[PaymentAttempt, Invoice]:
        # 1-2. Fetch (and lock) the invoice.
        invoice = self.invoice_repo.get_for_update(invoice_id)
        if invoice is None:
            raise NotFoundError(f"Invoice {invoice_id} not found")

        # 3. Validate before anything is written.
        amount = to_money(amount)
        if amount <= 0:
            raise BusinessRuleError("Payment amount must be greater than 0")
        if invoice.status not in PAYABLE_STATUSES:
            raise BusinessRuleError(f"Invoice {invoice.id} is {invoice.status.value} and cannot accept payments")
        if currency.upper() != invoice.currency:
            raise BusinessRuleError(f"Payment currency {currency} does not match invoice currency {invoice.currency}")
        if self.payment_attempt_repo.get_by_provider_reference(provider_reference) is not None:
            raise ConflictError(f"Payment with provider_reference {provider_reference} was already recorded")
        if status == PaymentStatus.SUCCESS and amount > invoice.amount_remaining:
            raise BusinessRuleError(
                f"Payment of {amount} exceeds the remaining unpaid amount {invoice.amount_remaining}"
            )

        # 4-5. Record the attempt. Failed attempts keep the reason and never touch amount_paid.
        attempt = self.payment_attempt_repo.add(
            PaymentAttempt(
                invoice_id=invoice.id,
                amount=amount,
                currency=invoice.currency,
                status=status,
                provider_reference=provider_reference,
                failure_reason=(failure_reason or "unspecified") if status == PaymentStatus.FAILED else None,
            )
        )

        # 6. Only successful payments move the invoice forward.
        if status == PaymentStatus.SUCCESS:
            invoice.amount_paid = to_money(invoice.amount_paid + amount)
            invoice.status = InvoiceStatus.PAID if invoice.amount_remaining == 0 else InvoiceStatus.PARTIALLY_PAID

        # 7. payment_success / payment_failure ledger entry, same transaction.
        self.ledger_service.record_payment_attempt(attempt, invoice)
        self.db.commit()
        return attempt, invoice

    def get_payment(self, payment_id: int) -> PaymentAttempt:
        attempt = self.payment_attempt_repo.get(payment_id)
        if attempt is None:
            raise NotFoundError(f"Payment attempt {payment_id} not found")
        return attempt

    def list_for_invoice(self, invoice_id: int) -> list[PaymentAttempt]:
        if self.invoice_repo.get(invoice_id) is None:
            raise NotFoundError(f"Invoice {invoice_id} not found")
        return self.payment_attempt_repo.list_for_invoice(invoice_id)
