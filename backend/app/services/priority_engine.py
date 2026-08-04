from datetime import datetime, timezone
from typing import Optional
from app.models.task import Task, TaskPriority, TaskStatus


class PriorityEngine:
    """
    Algorithmic Priority Score Calculator for Personal Task Manager Agent.

    Scoring formula:
    Priority Score = UrgencyScore + ImportanceScore + OverdueFactor + DurationFitFactor

    1. UrgencyScore:
       - No due date: 10 points
       - Due > 7 days: 20 points
       - Due within 7 days: 40 points
       - Due within 48 hours: 70 points
       - Due within 24 hours: 100 points

    2. ImportanceScore (Explicit user priority):
       - HIGH: 50 points
       - MEDIUM: 30 points
       - LOW: 10 points

    3. OverdueFactor:
       - Overdue tasks gain +80 points boost to prevent starvation.

    4. DurationFitFactor:
       - Shorter tasks (e.g. 15-30 mins) get slight momentum bonus (+10 points).
    """

    @staticmethod
    def calculate_score(task: Task, now: Optional[datetime] = None) -> float:
        if task.status == TaskStatus.COMPLETED or task.status == TaskStatus.CANCELLED:
            return 0.0

        if now is None:
            now = datetime.now(timezone.utc)

        # Ensure timezone alignment
        if task.due_date and task.due_date.tzinfo is None:
            due_date = task.due_date.replace(tzinfo=timezone.utc)
        else:
            due_date = task.due_date

        score = 0.0

        # 1. Importance Score
        if task.priority == TaskPriority.HIGH:
            score += 50.0
        elif task.priority == TaskPriority.MEDIUM:
            score += 30.0
        else:
            score += 10.0

        # 2. Urgency & Overdue Factor
        if due_date:
            time_until_due = (due_date - now).total_seconds() / 3600.0  # in hours

            if time_until_due < 0:
                # Task is overdue!
                hours_overdue = abs(time_until_due)
                overdue_boost = min(150.0, 80.0 + (hours_overdue * 2.0))
                score += overdue_boost
            elif time_until_due <= 24:
                score += 100.0
            elif time_until_due <= 48:
                score += 70.0
            elif time_until_due <= 168:  # 7 days
                score += 40.0
            else:
                score += 20.0
        else:
            score += 10.0

        # 3. Duration Fit (Quick wins get slight boost)
        if task.estimated_minutes and task.estimated_minutes <= 30:
            score += 10.0

        return round(score, 2)

    @classmethod
    def recalculate_task_priority(cls, task: Task, now: Optional[datetime] = None) -> float:
        score = cls.calculate_score(task, now)
        task.priority_score = score
        return score
