import pytest

from app.core.exceptions import LedgerImmutableError
from app.models import LedgerEntry


# Rule: partial payment -> partially_paid; full payment -> paid
def test_partial_then_full_payment_updates_status(client, make_invoice, pay):
    invoice = make_invoice()  # 499.00

    first = pay(invoice["id"], "200.00")
    assert first.status_code == 201
    assert first.json()["invoice"]["status"] == "partially_paid"
    assert first.json()["invoice"]["amount_paid"] == "200.00"
    assert first.json()["invoice"]["amount_remaining"] == "299.00"

    second = pay(invoice["id"], "299.00").json()
    assert second["invoice"]["status"] == "paid"
    assert second["invoice"]["amount_remaining"] == "0.00"


# Rule: successful payment cannot exceed remaining unpaid amount
def test_overpayment_is_rejected_and_not_recorded(client, make_invoice, pay):
    invoice = make_invoice()
    pay(invoice["id"], "400.00")

    resp = pay(invoice["id"], "100.00")  # only 99.00 remaining
    assert resp.status_code == 400
    assert "exceeds" in resp.json()["error"]["message"]

    attempts = client.get(f"/invoices/{invoice['id']}/payments").json()
    assert len(attempts) == 1
    assert client.get(f"/invoices/{invoice['id']}").json()["amount_paid"] == "400.00"


# Rule: failed payment does not increase amount_paid
def test_failed_payment_does_not_change_amount_paid(client, make_invoice, pay):
    invoice = make_invoice()
    resp = pay(invoice["id"], "499.00", status="failed", failure_reason="card_declined")
    assert resp.status_code == 201
    body = resp.json()
    assert body["payment_attempt"]["status"] == "failed"
    assert body["payment_attempt"]["failure_reason"] == "card_declined"
    assert body["invoice"]["amount_paid"] == "0.00"
    assert body["invoice"]["status"] == "issued"

    ledger = client.get("/ledger", params={"invoice_id": invoice["id"]}).json()
    assert [e["entry_type"] for e in ledger] == ["invoice_created", "payment_failure"]


def test_paid_invoice_rejects_further_payments(client, make_invoice, pay):
    invoice = make_invoice()
    pay(invoice["id"], "499.00")
    assert pay(invoice["id"], "1.00").status_code == 400


def test_duplicate_provider_reference_is_rejected(client, make_invoice, pay):
    invoice = make_invoice()
    assert pay(invoice["id"], "100.00", provider_reference="gw_123").status_code == 201
    dup = pay(invoice["id"], "100.00", provider_reference="gw_123")
    assert dup.status_code == 409
    assert client.get(f"/invoices/{invoice['id']}").json()["amount_paid"] == "100.00"


def test_currency_must_match_invoice(client, make_invoice, pay):
    invoice = make_invoice()
    assert pay(invoice["id"], "100.00", currency="USD").status_code == 400


def test_payment_for_unknown_invoice_returns_404(pay):
    assert pay(12345, "10.00").status_code == 404


# Rule: ledger entries are traceable through reference_id
def test_ledger_entries_trace_back_to_source(client, make_invoice, pay):
    invoice = make_invoice()
    attempt = pay(invoice["id"], "499.00").json()["payment_attempt"]

    entries = client.get(
        "/ledger", params={"reference_type": "payment_attempt", "reference_id": attempt["id"]}
    ).json()
    assert len(entries) == 1
    assert entries[0]["entry_type"] == "payment_success"
    assert entries[0]["amount"] == "499.00"
    assert entries[0]["invoice_id"] == invoice["id"]


def test_customer_balance_is_derived_from_ledger(client, make_customer, make_subscription, pay):
    customer = make_customer()
    sub = make_subscription(customer=customer)
    invoice = client.post("/invoices", json={"subscription_id": sub["id"]}).json()
    pay(invoice["id"], "100.00")
    pay(invoice["id"], "50.00", status="failed")

    balance = client.get(f"/customers/{customer['id']}/balance").json()
    assert balance["balances"] == [
        {"currency": "INR", "total_invoiced": "499.00", "total_paid": "100.00", "outstanding": "399.00"}
    ]


# Rule: ledger entries are append-only
def test_ledger_entries_cannot_be_updated_or_deleted(client, db_session, make_invoice):
    make_invoice()
    entry = db_session.query(LedgerEntry).first()

    entry.amount = 1
    with pytest.raises(LedgerImmutableError):
        db_session.flush()
    db_session.rollback()

    entry = db_session.query(LedgerEntry).first()
    db_session.delete(entry)
    with pytest.raises(LedgerImmutableError):
        db_session.flush()
    db_session.rollback()


def test_ledger_has_no_write_endpoints(client):
    assert client.post("/ledger", json={}).status_code == 405
