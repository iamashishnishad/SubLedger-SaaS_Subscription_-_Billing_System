from datetime import date

from sqlalchemy import select

from app.core.enums import InvoiceStatus
from app.models import Invoice
from app.repositories.base import BaseRepository


class InvoiceRepository(BaseRepository[Invoice]):
    model = Invoice

    def get_for_update(self, invoice_id: int) -> Invoice | None:
        # Row lock on Postgres so two concurrent payments can't both pass the
        # "remaining amount" check. SQLite ignores FOR UPDATE.
        stmt = select(Invoice).where(Invoice.id == invoice_id).with_for_update()
        return self.session.scalar(stmt)

    def get_by_subscription_and_period(self, subscription_id: int, period_start: date) -> Invoice | None:
        stmt = select(Invoice).where(
            Invoice.subscription_id == subscription_id,
            Invoice.period_start == period_start,
        )
        return self.session.scalar(stmt)

    def list_invoices(
        self,
        customer_id: int | None = None,
        subscription_id: int | None = None,
        status: InvoiceStatus | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Invoice]:
        stmt = select(Invoice).order_by(Invoice.id)
        if customer_id is not None:
            stmt = stmt.where(Invoice.customer_id == customer_id)
        if subscription_id is not None:
            stmt = stmt.where(Invoice.subscription_id == subscription_id)
        if status is not None:
            stmt = stmt.where(Invoice.status == status)
        return list(self.session.scalars(stmt.offset(offset).limit(limit)))
