from sqlalchemy import select

from app.models import PaymentAttempt
from app.repositories.base import BaseRepository


class PaymentAttemptRepository(BaseRepository[PaymentAttempt]):
    model = PaymentAttempt

    def get_by_provider_reference(self, provider_reference: str) -> PaymentAttempt | None:
        stmt = select(PaymentAttempt).where(PaymentAttempt.provider_reference == provider_reference)
        return self.session.scalar(stmt)

    def list_for_invoice(self, invoice_id: int) -> list[PaymentAttempt]:
        stmt = select(PaymentAttempt).where(PaymentAttempt.invoice_id == invoice_id).order_by(PaymentAttempt.id)
        return list(self.session.scalars(stmt))
