from fastapi import APIRouter

from app.api.routes import customers, invoices, ledger, payments, plans, subscriptions

api_router = APIRouter()
for module in (plans, customers, subscriptions, invoices, payments, ledger):
    api_router.include_router(module.router)
