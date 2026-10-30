# SubLedger: SaaS Subscription & Billing Backend

SubLedger is a small, layered billing backend. It manages **plans, customers, subscriptions, invoices, payment attempts, and an append-only ledger**. It is meant to be a clean foundation that is easy to read, test, and extend, not a Stripe clone.

- **Stack:** Python 3.12+, FastAPI, SQLAlchemy 2.0, Pydantic v2, PostgreSQL (Docker) or SQLite (local), pytest
- **Design document:** [DESIGN.md](DESIGN.md) covers the ERD, service and repository tables, business-rule ownership, design patterns, and the invoice and payment flows.

---

## Project structure

```
app/
├── main.py                 # FastAPI app, exception handlers, router wiring
├── config.py               # Settings (env vars / .env) via pydantic-settings
├── db.py                   # Engine, SessionLocal, Base, get_db dependency
├── core/
│   ├── enums.py            # Domain enums (statuses, entry types) + DB enum column helper
│   ├── billing.py          # Money rounding, billing-period date maths
│   └── exceptions.py       # DomainError hierarchy → HTTP status codes
├── models/                 # SQLAlchemy ORM models (tables, constraints, relationships)
├── schemas/                # Pydantic request/response models
├── repositories/           # Persistence only: queries, add/flush. No business rules.
├── services/               # Business rules + transaction boundaries
└── api/
    ├── deps.py             # Composition root: builds services per request (DI)
    └── routes/             # Thin HTTP layer: parse → call service → serialise
tests/                      # pytest, in-memory SQLite, 26 tests
```

## Setup

### Option A: Docker (PostgreSQL)

```bash
docker compose up --build
# API:      http://localhost:8000
# Swagger:  http://localhost:8000/docs
```

### Option B: Local (SQLite, no Docker)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env              # optional; defaults work as-is
uvicorn app.main:app --reload
# Swagger: http://127.0.0.1:8000/docs
```

Tables are created on startup. To use Postgres locally instead, set
`DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/subledger`.

### Run tests

```bash
pytest -q
```

### Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./subledger.db` | SQLAlchemy URL |
| `INVOICE_DUE_DAYS` | `7` | `due_date = period_start + N days` |
| `DEFAULT_CURRENCY` | `INR` | Default plan currency |
| `SQL_ECHO` | `false` | Log SQL statements |

## API list

Interactive docs are at **`/docs`** (Swagger UI) and **`/redoc`**.

### Postman collection

[`postman/`](postman/) contains a collection with 44 requests and an environment file:

1. In Postman, go to **Import** and select `postman/SubLedger.postman_collection.json` and `postman/SubLedger.local.postman_environment.json`.
2. Select the **SubLedger Local** environment (`baseUrl = http://localhost:8000`).
3. Right-click the collection, choose **Run collection**, and run it in order.

Each request saves the ids that later requests need (plan, customer, subscription, invoice and payment). The folders cover the happy path (Plans → Customers → Subscriptions → Invoices → Payments → Ledger), then **Business rule checks** (expected 4xx responses) and **Cancellation**. Every request has test assertions. A per-run `run_id` keeps emails and payment references unique, so you can re-run the collection without resetting the database.

From the CLI: `npx newman run postman/SubLedger.postman_collection.json -e postman/SubLedger.local.postman_environment.json`

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| **Plans** | | |
| POST | `/plans` | Create plan (`price > 0`) |
| GET | `/plans?active_only=` | List plans |
| GET | `/plans/{id}` | Get plan |
| PATCH | `/plans/{id}` | Update name/description/price/`is_active` |
| **Customers** | | |
| POST | `/customers` | Create customer (unique email) |
| GET | `/customers` | List customers |
| GET | `/customers/{id}` | Get customer |
| GET | `/customers/{id}/subscriptions` | Customer's subscriptions |
| GET | `/customers/{id}/invoices` | Customer's invoices |
| GET | `/customers/{id}/ledger` | Customer's ledger entries |
| GET | `/customers/{id}/balance` | Invoiced / paid / outstanding per currency, from the ledger |
| **Subscriptions** | | |
| POST | `/subscriptions` | Subscribe customer to an active plan |
| GET | `/subscriptions/{id}` | Get subscription |
| POST | `/subscriptions/{id}/cancel` | Cancel subscription |
| GET | `/subscriptions/{id}/invoices` | Subscription's invoices |
| **Invoices** | | |
| POST | `/invoices` | Generate invoice `{subscription_id, period_start?, period_end?}` |
| GET | `/invoices?customer_id=&subscription_id=&status=` | List invoices |
| GET | `/invoices/{id}` | Get invoice |
| GET | `/invoices/{id}/payments` | Payment attempts for invoice |
| GET | `/invoices/{id}/ledger` | Ledger entries for invoice |
| **Payments** | | |
| POST | `/payments` | Record attempt `{invoice_id, amount, currency, status, provider_reference, failure_reason?}` |
| GET | `/payments/{id}` | Get payment attempt |
| **Ledger** | | |
| GET | `/ledger?customer_id=&invoice_id=&reference_type=&reference_id=` | Read-only ledger query |

### Example flow

```bash
curl -X POST localhost:8000/plans -H 'Content-Type: application/json' \
  -d '{"name":"Pro","price":"999.00","currency":"INR","billing_interval":"monthly"}'
curl -X POST localhost:8000/customers -H 'Content-Type: application/json' \
  -d '{"name":"Asha","email":"asha@example.com"}'
curl -X POST localhost:8000/subscriptions -H 'Content-Type: application/json' \
  -d '{"customer_id":1,"plan_id":1}'
curl -X POST localhost:8000/invoices -H 'Content-Type: application/json' \
  -d '{"subscription_id":1}'
curl -X POST localhost:8000/payments -H 'Content-Type: application/json' \
  -d '{"invoice_id":1,"amount":"500.00","currency":"INR","status":"success","provider_reference":"pay_001"}'
curl localhost:8000/ledger?invoice_id=1
```

### Error format

All business errors share one shape:

```json
{ "error": { "code": "business_rule_violation", "message": "Payment of 1500.00 exceeds the remaining unpaid amount 999.00" } }
```

| Status | Code | When |
|---|---|---|
| 400 | `business_rule_violation` | Inactive plan, overpayment, invoice not payable, currency mismatch, cancelled subscription |
| 404 | `not_found` | Unknown id |
| 409 | `conflict` | Duplicate email, duplicate active subscription, duplicate invoice period, duplicate `provider_reference` |
| 422 | (FastAPI) | Request shape invalid, e.g. `price <= 0` or a malformed email |

Money is returned as **strings** (`"499.00"`) so no precision is lost to floating point.

## Assumptions

1. **Single currency per plan.** An invoice inherits the plan's currency, and a payment must be in the invoice's currency.
2. **Billing periods are half-open** `[period_start, period_end)`. Monthly adds one calendar month and clamps the day (Jan 31 → Feb 28). Yearly adds 12 months.
3. **Auto period:** if `POST /invoices` has no period, it bills the subscription's `current_period_*` and then advances the subscription to the next period. An explicit period does not move the subscription.
4. **Invoices are created as `issued`.** `draft` and `void` exist in the enum for future use.
5. **`due_date` = `period_start + INVOICE_DUE_DAYS`.**
6. **Grandfathering:** deactivating a plan blocks *new* subscriptions only. Existing active subscriptions on that plan can still be invoiced.
7. **Overpayment is rejected outright** rather than stored as credit. The rejected request is not recorded as an attempt. A *failed* attempt is always recorded, even when it is larger than the remaining amount, because nothing moved.
8. **`provider_reference` is globally unique.** This makes payment recording idempotent: a retried webhook gets `409` instead of a double-count.
9. Emails are normalised to lowercase, so uniqueness is case-insensitive.
10. No authentication or multi-tenancy (out of scope for the base version).

## Limitations / future work

- **No migrations.** Tables come from `create_all` on startup. Alembic is the next step.
- **Append-only is enforced in the ORM** (SQLAlchemy `before_update`/`before_delete` hooks) and by the repository API. Raw SQL could still modify rows; a Postgres trigger or `REVOKE UPDATE, DELETE` would close that gap.
- No refunds, credit notes, proration, plan upgrades/downgrades, taxes, discounts, or dunning/retry schedules.
- No scheduler: invoices are generated on demand via the API, not by a cron or worker.
- Concurrency: invoice and subscription rows are locked with `SELECT … FOR UPDATE` on Postgres. SQLite ignores this, so it is fine for local work but not for concurrent production use.
- Balance is computed on the fly from the ledger. At scale it would be a materialised or snapshotted value.
