from fastapi import APIRouter, Query

from app.api.deps import LedgerServiceDep
from app.core.enums import LedgerReferenceType
from app.schemas.ledger import LedgerEntryRead

router = APIRouter(prefix="/ledger", tags=["ledger"])


@router.get("", response_model=list[LedgerEntryRead])
def list_ledger_entries(
    service: LedgerServiceDep,
    customer_id: int | None = None,
    invoice_id: int | None = None,
    reference_type: LedgerReferenceType | None = None,
    reference_id: int | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    """Read-only. The ledger has no create/update/delete endpoints; entries are written by services."""
    return service.list_entries(
        customer_id=customer_id,
        invoice_id=invoice_id,
        reference_type=reference_type,
        reference_id=reference_id,
        offset=offset,
        limit=limit,
    )
