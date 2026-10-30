from decimal import Decimal

import pytest

from app.core.exceptions import BusinessRuleError
from app.repositories import PlanRepository
from app.schemas.plan import PlanCreate
from app.services import PlanService


# Rule: plan price must be greater than 0
@pytest.mark.parametrize("price", ["0", "-10.00"])
def test_plan_price_must_be_positive_via_api(client, price):
    resp = client.post("/plans", json={"name": "Free", "price": price, "currency": "INR"})
    assert resp.status_code == 422


def test_plan_price_must_be_positive_in_service(db_session):
    service = PlanService(db_session, PlanRepository(db_session))
    data = PlanCreate.model_construct(name="Bad", price=Decimal("0"), currency="INR")
    with pytest.raises(BusinessRuleError):
        service.create_plan(data)


# Rule: customer email must be unique (case-insensitive)
def test_customer_email_must_be_unique(client):
    first = client.post("/customers", json={"name": "A", "email": "Same@Example.com"})
    assert first.status_code == 201
    assert first.json()["email"] == "same@example.com"

    dup = client.post("/customers", json={"name": "B", "email": "same@example.COM"})
    assert dup.status_code == 409
    assert dup.json()["error"]["code"] == "conflict"


# Rule: cannot subscribe to an inactive plan
def test_cannot_subscribe_to_inactive_plan(client, make_plan, make_customer):
    plan = make_plan(is_active=False)
    customer = make_customer()
    resp = client.post("/subscriptions", json={"customer_id": customer["id"], "plan_id": plan["id"]})
    assert resp.status_code == 400
    assert "inactive" in resp.json()["error"]["message"]


def test_deactivated_plan_blocks_new_subscriptions(client, make_plan, make_customer):
    plan = make_plan()
    client.patch(f"/plans/{plan['id']}", json={"is_active": False})
    resp = client.post("/subscriptions", json={"customer_id": make_customer()["id"], "plan_id": plan["id"]})
    assert resp.status_code == 400


# Rule: no two active subscriptions to the same plan for one customer
def test_no_duplicate_active_subscription(client, make_plan, make_customer, make_subscription):
    plan, customer = make_plan(), make_customer()
    make_subscription(plan=plan, customer=customer)

    dup = client.post("/subscriptions", json={"customer_id": customer["id"], "plan_id": plan["id"]})
    assert dup.status_code == 409


def test_can_resubscribe_after_cancelling(client, make_plan, make_customer, make_subscription):
    plan, customer = make_plan(), make_customer()
    sub = make_subscription(plan=plan, customer=customer)
    assert client.post(f"/subscriptions/{sub['id']}/cancel").json()["status"] == "cancelled"

    again = client.post("/subscriptions", json={"customer_id": customer["id"], "plan_id": plan["id"]})
    assert again.status_code == 201


def test_subscription_requires_existing_customer_and_plan(client, make_plan):
    plan = make_plan()
    assert client.post("/subscriptions", json={"customer_id": 999, "plan_id": plan["id"]}).status_code == 404
