from fastapi import APIRouter, status

from app.api.deps import InvoiceServiceDep, SubscriptionServiceDep
from app.schemas.invoice import InvoiceRead
from app.schemas.subscription import SubscriptionCreate, SubscriptionRead

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post("", response_model=SubscriptionRead, status_code=status.HTTP_201_CREATED)
def create_subscription(data: SubscriptionCreate, service: SubscriptionServiceDep):
    return service.create_subscription(data)


@router.get("/{subscription_id}", response_model=SubscriptionRead)
def get_subscription(subscription_id: int, service: SubscriptionServiceDep):
    return service.get_subscription(subscription_id)


@router.post("/{subscription_id}/cancel", response_model=SubscriptionRead)
def cancel_subscription(subscription_id: int, service: SubscriptionServiceDep):
    return service.cancel_subscription(subscription_id)


@router.get("/{subscription_id}/invoices", response_model=list[InvoiceRead])
def list_subscription_invoices(
    subscription_id: int, subscriptions: SubscriptionServiceDep, invoices: InvoiceServiceDep
):
    subscriptions.get_subscription(subscription_id)
    return invoices.list_invoices(subscription_id=subscription_id)
