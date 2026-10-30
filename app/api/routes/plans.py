from fastapi import APIRouter, Query, status

from app.api.deps import PlanServiceDep
from app.schemas.plan import PlanCreate, PlanRead, PlanUpdate

router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("", response_model=PlanRead, status_code=status.HTTP_201_CREATED)
def create_plan(data: PlanCreate, service: PlanServiceDep):
    return service.create_plan(data)


@router.get("", response_model=list[PlanRead])
def list_plans(
    service: PlanServiceDep,
    active_only: bool = False,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    return service.list_plans(active_only=active_only, offset=offset, limit=limit)


@router.get("/{plan_id}", response_model=PlanRead)
def get_plan(plan_id: int, service: PlanServiceDep):
    return service.get_plan(plan_id)


@router.patch("/{plan_id}", response_model=PlanRead)
def update_plan(plan_id: int, data: PlanUpdate, service: PlanServiceDep):
    return service.update_plan(plan_id, data)
