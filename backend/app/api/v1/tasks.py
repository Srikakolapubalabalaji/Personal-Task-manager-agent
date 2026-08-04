from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.session import get_db
from app.models.user import User
from app.models.task import TaskStatus
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    SubtaskCreate,
    SubtaskUpdate,
    SubtaskResponse,
)
from app.services.task_service import TaskService
from app.api.deps import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=List[TaskResponse])
def get_tasks(
    status: Optional[TaskStatus] = None,
    category: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TaskService.get_user_tasks(db, current_user.id, status=status, category=category, limit=limit)


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TaskService.create_task(db, current_user.id, task_in)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = TaskService.get_task_by_id(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = TaskService.update_task(db, task_id, current_user.id, task_in)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    success = TaskService.delete_task(db, task_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")


@router.post("/{task_id}/complete", response_model=TaskResponse)
def complete_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = TaskService.complete_task(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{task_id}/subtasks", response_model=SubtaskResponse, status_code=status.HTTP_201_CREATED)
def add_subtask(
    task_id: str,
    subtask_in: SubtaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subtask = TaskService.add_subtask(db, task_id, current_user.id, subtask_in)
    if not subtask:
        raise HTTPException(status_code=404, detail="Task not found")
    return subtask


@router.put("/subtasks/{subtask_id}", response_model=SubtaskResponse)
def update_subtask(
    subtask_id: str,
    subtask_in: SubtaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    subtask = TaskService.update_subtask(db, subtask_id, current_user.id, subtask_in)
    if not subtask:
        raise HTTPException(status_code=404, detail="Subtask not found")
    return subtask


@router.post("/{task_id}/breakdown", response_model=TaskResponse)
def breakdown_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Intelligently breaks down a large task into concrete subtasks.
    """
    task = TaskService.get_task_by_id(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    title_lower = task.title.lower()
    default_subtasks = []

    if "interview" in title_lower or "prepare" in title_lower:
        default_subtasks = [
            "Revise fundamental concepts & core topics",
            "Review practical code examples & query optimization",
            "Study system design & architecture questions",
            "Practice mock interview questions & answers"
        ]
    elif "doc" in title_lower or "write" in title_lower or "project" in title_lower:
        default_subtasks = [
            "Outline document structure & section headers",
            "Draft core technical implementation section",
            "Include architectural flow diagrams & API endpoints",
            "Perform proofreading & final formatting pass"
        ]
    else:
        default_subtasks = [
            f"Step 1: Research & setup for {task.title}",
            f"Step 2: Core implementation work for {task.title}",
            f"Step 3: Testing & validation for {task.title}",
            f"Step 4: Finalize & mark complete"
        ]

    for sub_title in default_subtasks:
        TaskService.add_subtask(db, task.id, current_user.id, SubtaskCreate(title=sub_title))

    db.refresh(task)
    return task
