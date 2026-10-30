def test_invoice_amount_comes_from_plan_price_snapshot(client, make_plan, make_subscription):
    plan = make_plan(price="499.00")
    sub = make_subscription(plan=plan)

    first = client.post("/invoices", json={"subscription_id": sub["id"]}).json()
    assert first["amount_due"] == "499.00"
    assert first["amount_paid"] == "0.00"
    assert first["status"] == "issued"
    assert (first["period_start"], first["period_end"]) == ("2026-01-01", "2026-02-01")
    assert first["due_date"] == "2026-01-08"

    # Price change only applies to invoices generated afterwards.
    client.patch(f"/plans/{plan['id']}", json={"price": "799.00"})
    second = client.post("/invoices", json={"subscription_id": sub["id"]}).json()
    assert second["amount_due"] == "799.00"
    assert client.get(f"/invoices/{first['id']}").json()["amount_due"] == "499.00"


def test_auto_invoicing_advances_subscription_period(client, make_subscription):
    sub = make_subscription(start_date="2026-01-31")
    client.post("/invoices", json={"subscription_id": sub["id"]})
    refreshed = client.get(f"/subscriptions/{sub['id']}").json()
    assert refreshed["current_period_start"] == "2026-02-28"
    assert refreshed["current_period_end"] == "2026-03-28"


def test_cannot_invoice_same_period_twice(client, make_subscription):
    sub = make_subscription()
    body = {"subscription_id": sub["id"], "period_start": "2026-05-01", "period_end": "2026-06-01"}
    assert client.post("/invoices", json=body).status_code == 201
    assert client.post("/invoices", json=body).status_code == 409


def test_cannot_invoice_cancelled_subscription(client, make_subscription):
    sub = make_subscription()
    client.post(f"/subscriptions/{sub['id']}/cancel")
    resp = client.post("/invoices", json={"subscription_id": sub["id"]})
    assert resp.status_code == 400


def test_invoice_period_must_be_valid(client, make_subscription):
    sub = make_subscription()
    resp = client.post(
        "/invoices",
        json={"subscription_id": sub["id"], "period_start": "2026-06-01", "period_end": "2026-05-01"},
    )
    assert resp.status_code == 422


def test_invoice_creation_writes_ledger_entry(client, make_invoice):
    invoice = make_invoice()
    entries = client.get("/ledger", params={"reference_type": "invoice", "reference_id": invoice["id"]}).json()
    assert len(entries) == 1
    assert entries[0]["entry_type"] == "invoice_created"
    assert entries[0]["amount"] == invoice["amount_due"]
    assert entries[0]["invoice_id"] == invoice["id"]
