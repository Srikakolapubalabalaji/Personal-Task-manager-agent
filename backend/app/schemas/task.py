from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.task import TaskStatus, TaskPriority
from app.models.subtask import SubtaskStatus


class SubtaskBase(BaseModel):
    title: str


class SubtaskCreate(SubtaskBase):
    pass


class SubtaskUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[SubtaskStatus] = None


class SubtaskResponse(SubtaskBase):
    id: str
    task_id: str
    status: SubtaskStatus
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    estimated_minutes: int = Field(default=60, ge=5, le=1440)
    category: str = "General"


class TaskCreate(TaskBase):
    subtasks: Optional[List[str]] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    estimated_minutes: Optional[int] = None
    category: Optional[str] = None


class TaskResponse(TaskBase):
    id: str
    user_id: str
    status: TaskStatus
    priority_score: float
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    subtasks: List[SubtaskResponse] = []

    model_config = ConfigDict(from_attributes=True)
