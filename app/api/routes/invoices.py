from fastapi import APIRouter, Query, status

from app.api.deps import InvoiceServiceDep, LedgerServiceDep, PaymentServiceDep
from app.core.enums import InvoiceStatus
from app.schemas.invoice import InvoiceGenerate, InvoiceRead
from app.schemas.ledger import LedgerEntryRead
from app.schemas.payment import PaymentAttemptRead

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
def generate_invoice(data: InvoiceGenerate, service: InvoiceServiceDep):
    return service.generate_invoice(data.subscription_id, data.period_start, data.period_end)


@router.get("", response_model=list[InvoiceRead])
def list_invoices(
    service: InvoiceServiceDep,
    customer_id: int | None = None,
    subscription_id: int | None = None,
    status: InvoiceStatus | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return service.list_invoices(
        customer_id=customer_id, subscription_id=subscription_id, status=status, offset=offset, limit=limit
    )


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(invoice_id: int, service: InvoiceServiceDep):
    return service.get_invoice(invoice_id)


@router.get("/{invoice_id}/payments", response_model=list[PaymentAttemptRead])
def list_invoice_payments(invoice_id: int, service: PaymentServiceDep):
    return service.list_for_invoice(invoice_id)


@router.get("/{invoice_id}/ledger", response_model=list[LedgerEntryRead])
def list_invoice_ledger(invoice_id: int, invoices: InvoiceServiceDep, ledger: LedgerServiceDep):
    invoices.get_invoice(invoice_id)
    return ledger.list_entries(invoice_id=invoice_id, limit=1000)
