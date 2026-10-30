from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.db import Base, get_db
from app.main import app


@pytest.fixture
def db_session() -> Iterator[Session]:
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    def override_get_db() -> Iterator[Session]:
        try:
            yield db_session
        except Exception:
            db_session.rollback()
            raise

    app.dependency_overrides[get_db] = override_get_db
    # Not used as a context manager, so the lifespan (which touches the real DB) doesn't run.
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---- small helpers to keep tests readable --------------------------------


@pytest.fixture
def make_plan(client: TestClient):
    def _make(price: str = "499.00", is_active: bool = True, **extra) -> dict:
        payload = {"name": "Pro", "price": price, "currency": "INR", "is_active": is_active, **extra}
        resp = client.post("/plans", json=payload)
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make


@pytest.fixture
def make_customer(client: TestClient):
    counter = {"n": 0}

    def _make(email: str | None = None) -> dict:
        counter["n"] += 1
        resp = client.post(
            "/customers", json={"name": "Asha", "email": email or f"user{counter['n']}@example.com"}
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make


@pytest.fixture
def make_subscription(client: TestClient, make_plan, make_customer):
    def _make(plan: dict | None = None, customer: dict | None = None, start_date: str = "2026-01-01") -> dict:
        plan = plan or make_plan()
        customer = customer or make_customer()
        resp = client.post(
            "/subscriptions",
            json={"customer_id": customer["id"], "plan_id": plan["id"], "start_date": start_date},
        )
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make


@pytest.fixture
def make_invoice(client: TestClient, make_subscription):
    def _make(subscription: dict | None = None) -> dict:
        subscription = subscription or make_subscription()
        resp = client.post("/invoices", json={"subscription_id": subscription["id"]})
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make


@pytest.fixture
def pay(client: TestClient):
    counter = {"n": 0}

    def _pay(invoice_id: int, amount: str, status: str = "success", **extra):
        counter["n"] += 1
        payload = {
            "invoice_id": invoice_id,
            "amount": amount,
            "currency": "INR",
            "status": status,
            "provider_reference": f"pay_{counter['n']}",
            **extra,
        }
        return client.post("/payments", json=payload)

    return _pay
