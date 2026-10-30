from fastapi import APIRouter, Query, status

from app.api.deps import CustomerServiceDep, InvoiceServiceDep, LedgerServiceDep, SubscriptionServiceDep
from app.schemas.customer import CustomerBalance, CustomerCreate, CustomerRead
from app.schemas.invoice import InvoiceRead
from app.schemas.ledger import LedgerEntryRead
from app.schemas.subscription import SubscriptionRead

router = APIRouter(prefix="/customers", tags=["customers"])


@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(data: CustomerCreate, service: CustomerServiceDep):
    return service.create_customer(data)


@router.get("", response_model=list[CustomerRead])
def list_customers(
    service: CustomerServiceDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return service.list_customers(offset=offset, limit=limit)


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(customer_id: int, service: CustomerServiceDep):
    return service.get_customer(customer_id)


@router.get("/{customer_id}/subscriptions", response_model=list[SubscriptionRead])
def list_customer_subscriptions(customer_id: int, service: SubscriptionServiceDep):
    return service.list_for_customer(customer_id)


@router.get("/{customer_id}/invoices", response_model=list[InvoiceRead])
def list_customer_invoices(customer_id: int, customers: CustomerServiceDep, invoices: InvoiceServiceDep):
    customers.get_customer(customer_id)
    return invoices.list_invoices(customer_id=customer_id)


@router.get("/{customer_id}/ledger", response_model=list[LedgerEntryRead])
def list_customer_ledger(customer_id: int, customers: CustomerServiceDep, ledger: LedgerServiceDep):
    customers.get_customer(customer_id)
    return ledger.list_entries(customer_id=customer_id, limit=1000)


@router.get("/{customer_id}/balance", response_model=CustomerBalance)
def get_customer_balance(customer_id: int, customers: CustomerServiceDep, ledger: LedgerServiceDep):
    customers.get_customer(customer_id)
    return CustomerBalance(customer_id=customer_id, balances=ledger.customer_balances(customer_id))
