from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.schemas.task import TaskCreate, TaskUpdate, SubtaskCreate, SubtaskUpdate
from app.models.task import TaskPriority, TaskStatus
from app.services.task_service import TaskService
from app.services.calendar_service import CalendarService
from app.services.planner_service import PlannerService
from app.services.priority_engine import PriorityEngine


class AgentToolRunner:
    """
    Executes agent tools against the current user database and services,
    returning structured text/JSON responses to the LangGraph agent state.
    """

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id

    def create_task(
        self,
        title: str,
        description: Optional[str] = None,
        priority: str = "MEDIUM",
        due_date: Optional[str] = None,
        estimated_minutes: int = 60,
        category: str = "General",
        subtasks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        p_enum = TaskPriority.MEDIUM
        if priority.upper() == "HIGH":
            p_enum = TaskPriority.HIGH
        elif priority.upper() == "LOW":
            p_enum = TaskPriority.LOW

        parsed_due: Optional[datetime] = None
        if due_date:
            try:
                due_lower = due_date.lower()
                now = datetime.now(timezone.utc)
                if "tomorrow" in due_lower:
                    parsed_due = (now + timedelta(days=1)).replace(hour=17, minute=0, second=0)
                elif "today" in due_lower:
                    parsed_due = now.replace(hour=17, minute=0, second=0)
                elif "friday" in due_lower:
                    days_ahead = (4 - now.weekday()) % 7
                    if days_ahead == 0:
                        days_ahead = 7
                    parsed_due = (now + timedelta(days=days_ahead)).replace(hour=17, minute=0, second=0)
                else:
                    parsed_due = datetime.fromisoformat(due_date)
            except Exception:
                parsed_due = datetime.now(timezone.utc) + timedelta(days=1)

        task_in = TaskCreate(
            title=title,
            description=description,
            priority=p_enum,
            due_date=parsed_due,
            estimated_minutes=estimated_minutes,
            category=category,
            subtasks=subtasks
        )
        task = TaskService.create_task(self.db, self.user_id, task_in)
        return {
            "status": "success",
            "message": f"Created task '{task.title}'",
            "task_id": task.id,
            "priority": task.priority.value,
            "priority_score": task.priority_score,
            "due_date": task.due_date.strftime("%Y-%m-%d %H:%M") if task.due_date else "None",
            "estimated_minutes": task.estimated_minutes
        }

    def get_tasks(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        s_enum = None
        if status:
            try:
                s_enum = TaskStatus(status.upper())
            except ValueError:
                pass
        tasks = TaskService.get_user_tasks(self.db, self.user_id, status=s_enum)
        return [
            {
                "id": t.id,
                "title": t.title,
                "status": t.status.value,
                "priority": t.priority.value,
                "priority_score": t.priority_score,
                "due_date": t.due_date.strftime("%Y-%m-%d %H:%M") if t.due_date else "None",
                "estimated_minutes": t.estimated_minutes,
                "subtasks_count": len(t.subtasks)
            }
            for t in tasks
        ]

    def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        task = TaskService.get_task_by_id(self.db, task_id, self.user_id)
        if not task:
            return None
        return {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value,
            "priority": task.priority.value,
            "priority_score": task.priority_score,
            "due_date": task.due_date.strftime("%Y-%m-%d %H:%M") if task.due_date else None,
            "estimated_minutes": task.estimated_minutes,
            "category": task.category,
            "subtasks": [{"id": st.id, "title": st.title, "status": st.status.value} for st in task.subtasks]
        }

    def update_task(
        self,
        task_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
        estimated_minutes: Optional[int] = None,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        p_enum = None
        if priority:
            try:
                p_enum = TaskPriority(priority.upper())
            except ValueError:
                pass

        parsed_due = None
        if due_date:
            try:
                parsed_due = datetime.fromisoformat(due_date)
            except Exception:
                pass

        task_in = TaskUpdate(
            title=title,
            description=description,
            priority=p_enum,
            due_date=parsed_due,
            estimated_minutes=estimated_minutes,
            category=category
        )
        task = TaskService.update_task(self.db, task_id, self.user_id, task_in)
        if not task:
            return {"status": "error", "message": f"Task '{task_id}' not found"}
        return {"status": "success", "message": f"Updated task '{task.title}'", "task_id": task.id}

    def delete_task(self, task_id: str) -> Dict[str, Any]:
        success = TaskService.delete_task(self.db, task_id, self.user_id)
        if not success:
            return {"status": "error", "message": f"Task '{task_id}' not found"}
        return {"status": "success", "message": f"Deleted task '{task_id}'"}

    def complete_task(self, title_or_id: str) -> Dict[str, Any]:
        task = TaskService.get_task_by_id(self.db, title_or_id, self.user_id)
        if not task:
            tasks = TaskService.get_user_tasks(self.db, self.user_id)
            for t in tasks:
                if title_or_id.lower() in t.title.lower():
                    task = t
                    break
        if not task:
            return {"status": "error", "message": f"Task matching '{title_or_id}' not found"}

        completed = TaskService.complete_task(self.db, task.id, self.user_id)
        return {"status": "success", "message": f"Marked task '{completed.title}' as COMPLETED."}

    def create_subtask(self, task_id: str, title: str) -> Dict[str, Any]:
        subtask = TaskService.add_subtask(self.db, task_id, self.user_id, SubtaskCreate(title=title))
        if not subtask:
            return {"status": "error", "message": f"Task '{task_id}' not found"}
        return {"status": "success", "subtask_id": subtask.id, "title": subtask.title}

    def get_subtasks(self, task_id: str) -> List[Dict[str, Any]]:
        task = TaskService.get_task_by_id(self.db, task_id, self.user_id)
        if not task:
            return []
        return [{"id": st.id, "title": st.title, "status": st.status.value} for st in task.subtasks]

    def get_today_tasks(self) -> List[Dict[str, Any]]:
        tasks = TaskService.get_today_tasks(self.db, self.user_id)
        return [
            {
                "id": t.id,
                "title": t.title,
                "priority": t.priority.value,
                "priority_score": t.priority_score,
                "due_date": t.due_date.strftime("%Y-%m-%d %H:%M") if t.due_date else "Today"
            }
            for t in tasks
        ]

    def get_overdue_tasks(self) -> List[Dict[str, Any]]:
        tasks = TaskService.get_overdue_tasks(self.db, self.user_id)
        return [
            {
                "id": t.id,
                "title": t.title,
                "due_date": t.due_date.strftime("%Y-%m-%d %H:%M") if t.due_date else "Overdue",
                "priority": t.priority.value
            }
            for t in tasks
        ]

    def get_upcoming_tasks(self, days: int = 7) -> List[Dict[str, Any]]:
        tasks = TaskService.get_user_tasks(self.db, self.user_id, status=TaskStatus.PENDING)
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=days)
        upcoming = [t for t in tasks if t.due_date and t.due_date <= cutoff]
        return [
            {
                "id": t.id,
                "title": t.title,
                "due_date": t.due_date.strftime("%Y-%m-%d %H:%M"),
                "priority": t.priority.value
            }
            for t in upcoming
        ]

    def get_high_priority_tasks(self) -> List[Dict[str, Any]]:
        tasks = TaskService.get_user_tasks(self.db, self.user_id, status=TaskStatus.PENDING)
        high = [t for t in tasks if t.priority == TaskPriority.HIGH or t.priority_score >= 70.0]
        return [
            {
                "id": t.id,
                "title": t.title,
                "priority": t.priority.value,
                "priority_score": t.priority_score,
                "due_date": t.due_date.strftime("%Y-%m-%d %H:%M") if t.due_date else "None"
            }
            for t in high
        ]

    def get_calendar_events(self) -> List[Dict[str, Any]]:
        events = CalendarService.get_events(self.db, self.user_id)
        return [
            {
                "summary": e.summary,
                "time": f"{e.start.strftime('%H:%M')}–{e.end.strftime('%H:%M')}",
                "description": e.description
            }
            for e in events
        ]

    def get_available_time(self) -> List[Dict[str, Any]]:
        slots = CalendarService.get_available_time(self.db, self.user_id)
        return [
            {
                "start": s.start.strftime("%H:%M"),
                "end": s.end.strftime("%H:%M"),
                "duration_minutes": s.duration_minutes
            }
            for s in slots
        ]

    def generate_daily_plan(self) -> Dict[str, Any]:
        plan = PlannerService.generate_daily_plan(self.db, self.user_id)
        return {
            "date": plan.date,
            "available_hours": plan.available_hours,
            "required_task_hours": plan.required_task_hours,
            "is_overloaded": plan.is_overloaded,
            "schedule": [
                {
                    "item_type": slot.item_type,
                    "title": slot.title,
                    "time": f"{slot.start_time.strftime('%H:%M')}–{slot.end_time.strftime('%H:%M')}",
                    "reasoning": slot.reasoning
                }
                for slot in plan.schedule
            ],
            "recommendation": plan.recommendation
        }

    def generate_weekly_plan(self) -> Dict[str, Any]:
        plan = PlannerService.generate_weekly_plan(self.db, self.user_id)
        return {
            "start_date": plan.start_date,
            "end_date": plan.end_date,
            "recommendation": plan.weekly_recommendation,
            "days": [
                {
                    "day": d.day_name,
                    "date": d.date,
                    "tasks_count": d.total_tasks,
                    "hours": d.total_hours
                }
                for d in plan.days
            ]
        }

    def reschedule_task(self, task_id: str, target_date: Optional[str] = None) -> Dict[str, Any]:
        dt = None
        if target_date:
            try:
                dt = datetime.fromisoformat(target_date)
            except Exception:
                pass
        res = PlannerService.reschedule_task(self.db, self.user_id, task_id, dt)
        return {
            "task_id": res.task_id,
            "new_due_date": res.new_due_date,
            "message": res.message
        }

    def breakdown_task(self, title_or_id: str) -> Dict[str, Any]:
        task = TaskService.get_task_by_id(self.db, title_or_id, self.user_id)
        if not task:
            tasks = TaskService.get_user_tasks(self.db, self.user_id)
            for t in tasks:
                if title_or_id.lower() in t.title.lower():
                    task = t
                    break
        if not task:
            create_res = self.create_task(title=title_or_id, estimated_minutes=120)
            task_id = create_res["task_id"]
        else:
            task_id = task.id

        subtasks_list = [
            f"Step 1: Setup & outline key concepts for {title_or_id}",
            f"Step 2: Deep dive core implementation/topics",
            f"Step 3: Review code & edge cases",
            f"Step 4: Practice & test final output"
        ]

        for st in subtasks_list:
            TaskService.add_subtask(self.db, task_id, self.user_id, SubtaskCreate(title=st))

        return {
            "status": "success",
            "message": f"Broke task '{title_or_id}' into 4 subtasks.",
            "subtasks": subtasks_list
        }
