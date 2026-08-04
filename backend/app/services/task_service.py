from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.subtask import Subtask, SubtaskStatus
from app.schemas.task import TaskCreate, TaskUpdate, SubtaskCreate, SubtaskUpdate
from app.services.priority_engine import PriorityEngine
from app.services.deduplication import normalize_task_title


class TaskService:

    @staticmethod
    def get_user_tasks(
        db: Session,
        user_id: str,
        status: Optional[TaskStatus] = None,
        category: Optional[str] = None,
        limit: int = 100,
    ) -> List[Task]:
        query = db.query(Task).filter(Task.user_id == user_id)
        if status:
            query = query.filter(Task.status == status)
        if category:
            query = query.filter(Task.category == category)
        
        tasks = query.all()
        now = datetime.now(timezone.utc)
        for task in tasks:
            PriorityEngine.recalculate_task_priority(task, now)
        db.commit()

        tasks.sort(key=lambda t: t.priority_score, reverse=True)
        return tasks[:limit]

    @staticmethod
    def get_task_by_id(db: Session, task_id: str, user_id: str) -> Optional[Task]:
        task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
        if task:
            PriorityEngine.recalculate_task_priority(task)
            db.commit()
        return task

    @staticmethod
    def create_task(db: Session, user_id: str, task_in: TaskCreate) -> Task:
        now = datetime.now(timezone.utc)
        norm_title = normalize_task_title(task_in.title)

        # Check for existing PENDING task with identical normalized title
        existing_tasks = db.query(Task).filter(
            Task.user_id == user_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
        ).all()

        for ext in existing_tasks:
            if normalize_task_title(ext.title) == norm_title:
                # Deduplication hit: update existing task instead of creating duplicate row
                ext.priority = task_in.priority
                if task_in.due_date:
                    ext.due_date = task_in.due_date
                if task_in.estimated_minutes:
                    ext.estimated_minutes = task_in.estimated_minutes
                PriorityEngine.recalculate_task_priority(ext, now)
                db.commit()
                db.refresh(ext)
                return ext

        # Clean title before storing
        cleaned_title = task_in.title.strip()
        if cleaned_title.lower().startswith("create a task to "):
            cleaned_title = cleaned_title[len("create a task to "):].strip()
        elif cleaned_title.lower().startswith("create task to "):
            cleaned_title = cleaned_title[len("create task to "):].strip()
        elif cleaned_title.lower().startswith("create task "):
            cleaned_title = cleaned_title[len("create task "):].strip()

        task = Task(
            user_id=user_id,
            title=cleaned_title,
            description=task_in.description,
            priority=task_in.priority,
            due_date=task_in.due_date,
            estimated_minutes=task_in.estimated_minutes,
            category=task_in.category,
            status=TaskStatus.PENDING,
        )
        db.add(task)
        db.flush()

        if task_in.subtasks:
            for sub_title in task_in.subtasks:
                sub = Subtask(task_id=task.id, title=sub_title, status=SubtaskStatus.PENDING)
                db.add(sub)

        PriorityEngine.recalculate_task_priority(task, now)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def update_task(db: Session, task_id: str, user_id: str, task_in: TaskUpdate) -> Optional[Task]:
        task = TaskService.get_task_by_id(db, task_id, user_id)
        if not task:
            return None

        update_data = task_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        if task.status == TaskStatus.COMPLETED and not task.completed_at:
            task.completed_at = datetime.now(timezone.utc)
        elif task.status != TaskStatus.COMPLETED:
            task.completed_at = None

        PriorityEngine.recalculate_task_priority(task)
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def delete_task(db: Session, task_id: str, user_id: str) -> bool:
        task = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
        if not task:
            return False
        db.delete(task)
        db.commit()
        return True

    @staticmethod
    def complete_task(db: Session, task_id: str, user_id: str) -> Optional[Task]:
        task = TaskService.get_task_by_id(db, task_id, user_id)
        if not task:
            return None
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc)
        for subtask in task.subtasks:
            subtask.status = SubtaskStatus.COMPLETED
            subtask.completed_at = datetime.now(timezone.utc)

        task.priority_score = 0.0
        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def add_subtask(db: Session, task_id: str, user_id: str, subtask_in: SubtaskCreate) -> Optional[Subtask]:
        task = TaskService.get_task_by_id(db, task_id, user_id)
        if not task:
            return None
        subtask = Subtask(task_id=task.id, title=subtask_in.title, status=SubtaskStatus.PENDING)
        db.add(subtask)
        db.commit()
        db.refresh(subtask)
        return subtask

    @staticmethod
    def update_subtask(
        db: Session, subtask_id: str, user_id: str, subtask_in: SubtaskUpdate
    ) -> Optional[Subtask]:
        subtask = db.query(Subtask).join(Task).filter(Subtask.id == subtask_id, Task.user_id == user_id).first()
        if not subtask:
            return None

        update_data = subtask_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(subtask, field, value)

        if subtask.status == SubtaskStatus.COMPLETED and not subtask.completed_at:
            subtask.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(subtask)
        return subtask

    @staticmethod
    def get_overdue_tasks(db: Session, user_id: str) -> List[Task]:
        now = datetime.now(timezone.utc)
        tasks = (
            db.query(Task)
            .filter(
                Task.user_id == user_id,
                Task.status == TaskStatus.PENDING,
                Task.due_date < now
            )
            .all()
        )
        return tasks

    @staticmethod
    def get_today_tasks(db: Session, user_id: str) -> List[Task]:
        now = datetime.now(timezone.utc)
        end_of_today = datetime(now.year, now.month, now.day, 23, 59, 59, tzinfo=timezone.utc)
        tasks = (
            db.query(Task)
            .filter(
                Task.user_id == user_id,
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                Task.due_date <= end_of_today
            )
            .all()
        )
        for t in tasks:
            PriorityEngine.recalculate_task_priority(t, now)
        tasks.sort(key=lambda t: t.priority_score, reverse=True)

        # Apply deduplication filter
        seen = set()
        unique = []
        for t in tasks:
            norm = normalize_task_title(t.title)
            if norm not in seen:
                seen.add(norm)
                unique.append(t)
        return unique
