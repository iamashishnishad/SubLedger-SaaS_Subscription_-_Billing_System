from fastapi import APIRouter, status

from app.api.deps import PaymentServiceDep
from app.schemas.payment import PaymentAttemptRead, PaymentCreate, PaymentResult

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentResult, status_code=status.HTTP_201_CREATED)
def record_payment(data: PaymentCreate, service: PaymentServiceDep):
    attempt, invoice = service.record_payment(
        invoice_id=data.invoice_id,
        amount=data.amount,
        currency=data.currency,
        status=data.status,
        provider_reference=data.provider_reference,
        failure_reason=data.failure_reason,
    )
    return PaymentResult(
        payment_attempt=PaymentAttemptRead.model_validate(attempt),
        invoice=invoice,
    )


@router.get("/{payment_id}", response_model=PaymentAttemptRead)
def get_payment(payment_id: int, service: PaymentServiceDep):
    return service.get_payment(payment_id)
