from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.database.session import get_db
from app.models.user import User
from app.schemas.planner import DailyPlanResponse, WeeklyPlanResponse, RescheduleRequest, RescheduleResponse
from app.services.planner_service import PlannerService
from app.api.deps import get_current_user

router = APIRouter(prefix="/planner", tags=["planner"])


@router.get("/today", response_model=DailyPlanResponse)
def get_daily_plan(
    target_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return PlannerService.generate_daily_plan(db, current_user.id, target_date=target_date)


@router.get("/week", response_model=WeeklyPlanResponse)
def get_weekly_plan(
    start_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return PlannerService.generate_weekly_plan(db, current_user.id, start_date=start_date)


@router.post("/reschedule", response_model=RescheduleResponse)
def reschedule_task(
    req: RescheduleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return PlannerService.reschedule_task(db, current_user.id, req.task_id, req.target_date)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
