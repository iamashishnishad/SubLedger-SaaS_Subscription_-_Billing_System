from collections import defaultdict
from decimal import Decimal

from app.core.billing import to_money
from app.core.enums import LedgerEntryType, LedgerReferenceType, PaymentStatus
from app.models import Invoice, LedgerEntry, PaymentAttempt
from app.repositories import LedgerEntryRepository
from app.schemas.customer import CurrencyBalance


class LedgerService:
    """Single writer for ledger entries.

    It never commits: entries are written inside the caller's transaction so an
    invoice/payment and its ledger entry are saved together or not at all.
    """

    def __init__(self, ledger_repo: LedgerEntryRepository):
        self.ledger_repo = ledger_repo

    def record_invoice_created(self, invoice: Invoice) -> LedgerEntry:
        return self.ledger_repo.add(
            LedgerEntry(
                customer_id=invoice.customer_id,
                invoice_id=invoice.id,
                entry_type=LedgerEntryType.INVOICE_CREATED,
                amount=invoice.amount_due,
                currency=invoice.currency,
                reference_type=LedgerReferenceType.INVOICE,
                reference_id=invoice.id,
                description=f"Invoice {invoice.id} for {invoice.period_start} to {invoice.period_end}",
            )
        )

    def record_payment_attempt(self, attempt: PaymentAttempt, invoice: Invoice) -> LedgerEntry:
        succeeded = attempt.status == PaymentStatus.SUCCESS
        if succeeded:
            description = f"Payment {attempt.provider_reference} received for invoice {invoice.id}"
        else:
            description = f"Payment {attempt.provider_reference} failed: {attempt.failure_reason}"
        return self.ledger_repo.add(
            LedgerEntry(
                customer_id=invoice.customer_id,
                invoice_id=invoice.id,
                entry_type=LedgerEntryType.PAYMENT_SUCCESS if succeeded else LedgerEntryType.PAYMENT_FAILURE,
                # For failures this is the attempted amount, kept for audit; it never counts toward balance.
                amount=attempt.amount,
                currency=attempt.currency,
                reference_type=LedgerReferenceType.PAYMENT_ATTEMPT,
                reference_id=attempt.id,
                description=description[:255],
            )
        )

    def list_entries(self, **filters) -> list[LedgerEntry]:
        return self.ledger_repo.list_entries(**filters)

    def customer_balances(self, customer_id: int) -> list[CurrencyBalance]:
        """Outstanding balance per currency, derived purely from the ledger."""
        totals: dict[str, dict[LedgerEntryType, Decimal]] = defaultdict(dict)
        for currency, entry_type, total in self.ledger_repo.sum_by_currency_and_type(customer_id):
            totals[currency][entry_type] = to_money(total)
        balances = []
        for currency, by_type in sorted(totals.items()):
            invoiced = by_type.get(LedgerEntryType.INVOICE_CREATED, Decimal("0.00"))
            paid = by_type.get(LedgerEntryType.PAYMENT_SUCCESS, Decimal("0.00"))
            balances.append(
                CurrencyBalance(currency=currency, total_invoiced=invoiced, total_paid=paid, outstanding=invoiced - paid)
            )
        return balances
