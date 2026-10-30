from decimal import Decimal

from sqlalchemy import func, select

from app.core.enums import LedgerEntryType, LedgerReferenceType
from app.models import LedgerEntry
from app.repositories.base import BaseRepository


class LedgerEntryRepository(BaseRepository[LedgerEntry]):
    """Append-only: exposes add/read methods only. No update or delete on purpose."""

    model = LedgerEntry

    def list_entries(
        self,
        customer_id: int | None = None,
        invoice_id: int | None = None,
        reference_type: LedgerReferenceType | None = None,
        reference_id: int | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[LedgerEntry]:
        stmt = select(LedgerEntry).order_by(LedgerEntry.id)
        if customer_id is not None:
            stmt = stmt.where(LedgerEntry.customer_id == customer_id)
        if invoice_id is not None:
            stmt = stmt.where(LedgerEntry.invoice_id == invoice_id)
        if reference_type is not None:
            stmt = stmt.where(LedgerEntry.reference_type == reference_type)
        if reference_id is not None:
            stmt = stmt.where(LedgerEntry.reference_id == reference_id)
        return list(self.session.scalars(stmt.offset(offset).limit(limit)))

    def sum_by_currency_and_type(self, customer_id: int) -> list[tuple[str, LedgerEntryType, Decimal]]:
        stmt = (
            select(LedgerEntry.currency, LedgerEntry.entry_type, func.sum(LedgerEntry.amount))
            .where(LedgerEntry.customer_id == customer_id)
            .group_by(LedgerEntry.currency, LedgerEntry.entry_type)
        )
        return [tuple(row) for row in self.session.execute(stmt)]
