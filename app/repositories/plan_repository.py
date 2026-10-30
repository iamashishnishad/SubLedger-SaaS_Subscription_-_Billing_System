from sqlalchemy import select

from app.models import Plan
from app.repositories.base import BaseRepository


class PlanRepository(BaseRepository[Plan]):
    model = Plan

    def list_plans(self, active_only: bool = False, offset: int = 0, limit: int = 100) -> list[Plan]:
        stmt = select(Plan).order_by(Plan.id)
        if active_only:
            stmt = stmt.where(Plan.is_active.is_(True))
        return list(self.session.scalars(stmt.offset(offset).limit(limit)))
