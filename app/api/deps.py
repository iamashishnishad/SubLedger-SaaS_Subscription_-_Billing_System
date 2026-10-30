"""Composition root: builds services from repositories for each request."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.repositories import (
    CustomerRepository,
    InvoiceRepository,
    LedgerEntryRepository,
    PaymentAttemptRepository,
    PlanRepository,
    SubscriptionRepository,
)
from app.services import (
    CustomerService,
    InvoiceService,
    LedgerService,
    PaymentService,
    PlanService,
    SubscriptionService,
)

DbSession = Annotated[Session, Depends(get_db)]


def get_plan_service(db: DbSession) -> PlanService:
    return PlanService(db, PlanRepository(db))


def get_customer_service(db: DbSession) -> CustomerService:
    return CustomerService(db, CustomerRepository(db))


def get_subscription_service(db: DbSession) -> SubscriptionService:
    return SubscriptionService(db, SubscriptionRepository(db), CustomerRepository(db), PlanRepository(db))


def get_ledger_service(db: DbSession) -> LedgerService:
    return LedgerService(LedgerEntryRepository(db))


def get_invoice_service(db: DbSession) -> InvoiceService:
    return InvoiceService(
        db,
        SubscriptionRepository(db),
        PlanRepository(db),
        InvoiceRepository(db),
        LedgerService(LedgerEntryRepository(db)),
    )


def get_payment_service(db: DbSession) -> PaymentService:
    return PaymentService(
        db,
        InvoiceRepository(db),
        PaymentAttemptRepository(db),
        LedgerService(LedgerEntryRepository(db)),
    )


PlanServiceDep = Annotated[PlanService, Depends(get_plan_service)]
CustomerServiceDep = Annotated[CustomerService, Depends(get_customer_service)]
SubscriptionServiceDep = Annotated[SubscriptionService, Depends(get_subscription_service)]
LedgerServiceDep = Annotated[LedgerService, Depends(get_ledger_service)]
InvoiceServiceDep = Annotated[InvoiceService, Depends(get_invoice_service)]
PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]
