from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.task import Task, TaskStatus, TaskPriority
from app.schemas.planner import (
    DailyPlanResponse,
    ScheduledSlot,
    WeeklyPlanResponse,
    DaySummary,
    RescheduleResponse,
)
from app.schemas.task import TaskResponse
from app.services.task_service import TaskService
from app.services.calendar_service import CalendarService
from app.services.priority_engine import PriorityEngine
from app.services.deduplication import normalize_task_title


class PlannerService:

    @staticmethod
    def generate_daily_plan(
        db: Session, user_id: str, target_date: Optional[datetime] = None
    ) -> DailyPlanResponse:
        if not target_date:
            target_date = datetime.now()

        day_start = datetime(target_date.year, target_date.month, target_date.day, 9, 0, 0)
        day_end = datetime(target_date.year, target_date.month, target_date.day, 18, 0, 0)
        date_str = day_start.strftime("%Y-%m-%d")

        # 1. Retrieve Calendar Events & Availability
        events = CalendarService.get_events(db, user_id, start_date=day_start, end_date=day_end)
        events.sort(key=lambda e: e.start)

        free_slots = CalendarService.get_available_time(db, user_id, target_date=day_start)
        total_available_minutes = sum(s.duration_minutes for s in free_slots)
        available_hours = round(total_available_minutes / 60.0, 1)

        # 2. Retrieve Pending & In-Progress Tasks
        pending_tasks = TaskService.get_user_tasks(db, user_id, status=TaskStatus.PENDING)
        in_progress_tasks = TaskService.get_user_tasks(db, user_id, status=TaskStatus.IN_PROGRESS)
        all_candidate_tasks = in_progress_tasks + pending_tasks

        now = datetime.now(timezone.utc)
        for t in all_candidate_tasks:
            PriorityEngine.recalculate_task_priority(t, now)

        all_candidate_tasks.sort(key=lambda t: t.priority_score, reverse=True)

        # Deduplication
        seen_normalized_titles = set()
        unique_candidate_tasks: List[Task] = []
        for t in all_candidate_tasks:
            norm_title = normalize_task_title(t.title)
            if norm_title not in seen_normalized_titles:
                seen_normalized_titles.add(norm_title)
                unique_candidate_tasks.append(t)
        all_candidate_tasks = unique_candidate_tasks

        overdue_tasks = TaskService.get_overdue_tasks(db, user_id)
        overdue_count = len(overdue_tasks)

        total_required_minutes = sum(t.estimated_minutes for t in all_candidate_tasks)
        required_task_hours = round(total_required_minutes / 60.0, 1)

        # 3. Schedule Interval Packing into Free Slots
        schedule: List[ScheduledSlot] = []
        
        task_queue = []
        for t in all_candidate_tasks:
            task_queue.append({
                "id": t.id,
                "title": t.title,
                "priority": t.priority.value,
                "priority_score": t.priority_score,
                "remaining_minutes": t.estimated_minutes,
                "original_task": t,
                "part": 1
            })

        for free_slot in free_slots:
            slot_cursor = free_slot.start
            slot_end = free_slot.end

            while slot_cursor < slot_end and task_queue:
                avail_mins = int((slot_end - slot_cursor).total_seconds() / 60)
                if avail_mins < 15:
                    break

                item = task_queue[0]
                task_dur = item["remaining_minutes"]

                if task_dur <= avail_mins:
                    item = task_queue.pop(0)
                    t_start = slot_cursor
                    t_end = t_start + timedelta(minutes=task_dur)
                    
                    title = item["title"] if item["part"] == 1 else f"{item['title']} (Part {item['part']})"
                    
                    schedule.append(
                        ScheduledSlot(
                            item_type="TASK",
                            id=item["id"],
                            title=title,
                            start_time=t_start,
                            end_time=t_end,
                            duration_minutes=task_dur,
                            priority=item["priority"],
                            reasoning=f"Prioritized due to score {item['priority_score']:.1f}",
                            time=f"{t_start.strftime('%H:%M')}–{t_end.strftime('%H:%M')}"
                        )
                    )
                    slot_cursor = t_end
                    if slot_cursor + timedelta(minutes=5) <= slot_end:
                        slot_cursor += timedelta(minutes=5)
                    else:
                        slot_cursor = slot_end
                else:
                    if avail_mins >= 30:
                        part_dur = avail_mins
                        item["remaining_minutes"] -= part_dur
                        t_start = slot_cursor
                        t_end = slot_end
                        
                        title = f"{item['title']} (Part {item['part']})"
                        item["part"] += 1
                        
                        schedule.append(
                            ScheduledSlot(
                                item_type="TASK",
                                id=item["id"],
                                title=title,
                                start_time=t_start,
                                end_time=t_end,
                                duration_minutes=part_dur,
                                priority=item["priority"],
                                reasoning=f"Allocated initial {part_dur} mins slot",
                                time=f"{t_start.strftime('%H:%M')}–{t_end.strftime('%H:%M')}"
                            )
                        )
                        slot_cursor = slot_end
                    else:
                        break

        # 4. Insert Calendar Events into schedule timeline
        for event in events:
            schedule.append(
                ScheduledSlot(
                    item_type="EVENT",
                    id=event.id,
                    title=event.summary,
                    start_time=event.start,
                    end_time=event.end,
                    duration_minutes=int((event.end - event.start).total_seconds() / 60),
                    reasoning="Calendar Appointment / Meeting",
                    time=f"{event.start.strftime('%H:%M')}–{event.end.strftime('%H:%M')}"
                )
            )

        # Sort combined timeline by start_time
        schedule.sort(key=lambda s: s.start_time)

        # Identify unscheduled tasks
        unscheduled_task_ids = {item["id"] for item in task_queue}
        unscheduled_tasks = [t for t in all_candidate_tasks if t.id in unscheduled_task_ids]

        is_overloaded = required_task_hours > available_hours or len(unscheduled_tasks) > 0

        if is_overloaded:
            top_task_title = all_candidate_tasks[0].title if all_candidate_tasks else "high-priority tasks"
            recommendation = (
                f"Workload ({required_task_hours} hrs) exceeds available focus time ({available_hours} hrs). "
                f"Start immediately with '{top_task_title}' as it has the highest priority score. "
                f"Move {len(unscheduled_tasks)} lower priority task(s) to tomorrow."
            )
        elif all_candidate_tasks:
            top_task_title = all_candidate_tasks[0].title
            recommendation = (
                f"Realistic plan generated for {date_str}! You have {available_hours} available hours. "
                f"Start with '{top_task_title}' to maximize focus on key deadlines."
            )
        else:
            recommendation = "All pending tasks completed! Enjoy your open calendar."

        return DailyPlanResponse(
            date=date_str,
            available_hours=available_hours,
            required_task_hours=required_task_hours,
            is_overloaded=is_overloaded,
            tasks_count=len(all_candidate_tasks),
            overdue_count=overdue_count,
            schedule=schedule,
            recommendation=recommendation,
            unscheduled_tasks=[TaskResponse.model_validate(t) for t in unscheduled_tasks]
        )

    @staticmethod
    def generate_weekly_plan(
        db: Session, user_id: str, start_date: Optional[datetime] = None
    ) -> WeeklyPlanResponse:
        if not start_date:
            start_date = datetime.now(timezone.utc)

        days: List[DaySummary] = []
        pending_tasks = TaskService.get_user_tasks(db, user_id, status=TaskStatus.PENDING)

        # Apply deduplication for weekly plan as well
        seen = set()
        unique = []
        for t in pending_tasks:
            norm = normalize_task_title(t.title)
            if norm not in seen:
                seen.add(norm)
                unique.append(t)
        pending_tasks = unique

        for i in range(5):  # 5 workdays (Mon-Fri)
            curr_date = start_date + timedelta(days=i)
            day_name = curr_date.strftime("%A")
            date_str = curr_date.strftime("%Y-%m-%d")

            events = CalendarService.get_events(
                db, user_id,
                start_date=curr_date.replace(hour=9, minute=0),
                end_date=curr_date.replace(hour=18, minute=0)
            )

            day_tasks = pending_tasks[i * 2 : (i + 1) * 2]
            day_hours = sum(t.estimated_minutes for t in day_tasks) / 60.0

            days.append(
                DaySummary(
                    date=date_str,
                    day_name=day_name,
                    total_tasks=len(day_tasks),
                    total_hours=round(day_hours, 1),
                    events=events,
                    top_tasks=[TaskResponse.model_validate(t) for t in day_tasks]
                )
            )

        start_str = start_date.strftime("%Y-%m-%d")
        end_str = (start_date + timedelta(days=4)).strftime("%Y-%m-%d")

        return WeeklyPlanResponse(
            start_date=start_str,
            end_date=end_str,
            days=days,
            weekly_recommendation=(
                f"Weekly workload distributed across 5 days. Ensure high-effort tasks "
                f"are scheduled earlier in the week to avoid deadline bottlenecks."
            )
        )

    @staticmethod
    def reschedule_task(
        db: Session, user_id: str, task_id: str, target_date: Optional[datetime] = None
    ) -> RescheduleResponse:
        if not target_date:
            target_date = datetime.now(timezone.utc) + timedelta(days=1)

        task = TaskService.get_task_by_id(db, task_id, user_id)
        if not task:
            raise ValueError(f"Task with ID {task_id} not found")

        task.due_date = target_date
        PriorityEngine.recalculate_task_priority(task)
        db.commit()

        target_str = target_date.strftime("%Y-%m-%d %H:%M")
        return RescheduleResponse(
            task_id=task.id,
            new_due_date=target_str,
            message=f"Successfully rescheduled '{task.title}' to {target_str}."
        )
