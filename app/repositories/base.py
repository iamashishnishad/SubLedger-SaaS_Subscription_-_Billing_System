from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    """Persistence-only access for one model. No business rules live here.

    Repositories flush (so generated ids are available) but never commit;
    the calling service decides when a unit of work is complete.
    """

    model: type[ModelT]

    def __init__(self, session: Session):
        self.session = session

    def get(self, entity_id: int) -> ModelT | None:
        return self.session.get(self.model, entity_id)

    def add(self, entity: ModelT) -> ModelT:
        self.session.add(entity)
        self.session.flush()
        return entity

    def list(self, offset: int = 0, limit: int = 100) -> list[ModelT]:
        stmt = select(self.model).order_by(self.model.id).offset(offset).limit(limit)
        return list(self.session.scalars(stmt))
