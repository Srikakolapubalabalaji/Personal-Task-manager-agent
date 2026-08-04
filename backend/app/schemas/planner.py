from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.schemas.task import TaskResponse
from app.schemas.calendar import CalendarEvent


class ScheduledSlot(BaseModel):
    item_type: str  # "TASK" or "EVENT" or "BREAK"
    id: str
    title: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    priority: Optional[str] = None
    reasoning: Optional[str] = None
    time: Optional[str] = None


class DailyPlanResponse(BaseModel):
    date: str
    available_hours: float
    required_task_hours: float
    is_overloaded: bool
    tasks_count: int
    overdue_count: int
    schedule: List[ScheduledSlot]
    recommendation: str
    unscheduled_tasks: List[TaskResponse] = []


class DaySummary(BaseModel):
    date: str
    day_name: str
    total_tasks: int
    total_hours: float
    events: List[CalendarEvent]
    top_tasks: List[TaskResponse]


class WeeklyPlanResponse(BaseModel):
    start_date: str
    end_date: str
    days: List[DaySummary]
    weekly_recommendation: str


class RescheduleRequest(BaseModel):
    task_id: str
    target_date: Optional[datetime] = None


class RescheduleResponse(BaseModel):
    task_id: str
    new_due_date: str
    message: str
