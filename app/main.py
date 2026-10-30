from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api.routes import api_router
from app.config import get_settings
from app.core.exceptions import DomainError
from app.db import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title=get_settings().app_name,
    description="SaaS subscription & billing backend: plans, customers, subscriptions, invoices, payments, ledger.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(DomainError)
async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})


@app.exception_handler(IntegrityError)
async def integrity_error_handler(_: Request, exc: IntegrityError) -> JSONResponse:
    # Safety net for races the service-level checks can't see (e.g. two
    # simultaneous sign-ups with the same email). The DB constraint wins.
    return JSONResponse(
        status_code=409,
        content={"error": {"code": "conflict", "message": "Request conflicts with existing data"}},
    )


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
