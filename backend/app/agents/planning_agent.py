import json
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from app.tools.task_tools import AgentToolRunner
from app.schemas.agent import ToolCallTrace


class PlanningAgent:
    """
    Intelligent Planning Agent using Tool Routing & Execution Flow.
    Reads real database tasks, Google calendar events, priority scores,
    and returns context-aware plans and actions.
    """

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
        self.runner = AgentToolRunner(db, user_id)

    def process_message(self, user_message: str) -> Tuple[str, List[ToolCallTrace]]:
        msg_lower = user_message.lower()
        tool_traces: List[ToolCallTrace] = []

        # 1. Query: "Do I have enough time to finish my tasks today?"
        if "enough time" in msg_lower or "time to finish" in msg_lower:
            daily_plan = self.runner.generate_daily_plan()
            tool_traces.append(
                ToolCallTrace(tool_name="generate_daily_plan", arguments={}, output=daily_plan)
            )

            avail = daily_plan["available_hours"]
            req = daily_plan["required_task_hours"]
            is_overloaded = daily_plan["is_overloaded"]

            if is_overloaded:
                diff = round(req - avail, 1)
                response = (
                    f"⚠️ **No, your workload currently exceeds your available time.**\n\n"
                    f"- **Available Focus Time:** {avail} hours\n"
                    f"- **Required Effort:** {req} hours\n"
                    f"- **Time Deficit:** {diff} hours\n\n"
                    f"**Agent Recommendation:**\n{daily_plan['recommendation']}"
                )
            else:
                remaining = round(avail - req, 1)
                response = (
                    f"✅ **Yes, you have enough time to complete today's planned tasks!**\n\n"
                    f"- **Available Focus Time:** {avail} hours\n"
                    f"- **Required Effort:** {req} hours\n"
                    f"- **Buffer Remaining:** {remaining} hours\n\n"
                    f"Start with your highest priority items first to make steady progress."
                )
            return response, tool_traces

        # 2. Query: "Move my task to tomorrow" / "Reschedule..."
        elif "move" in msg_lower or "reschedule" in msg_lower:
            tasks = self.runner.get_tasks(status="PENDING")
            tool_traces.append(
                ToolCallTrace(tool_name="get_tasks", arguments={"status": "PENDING"}, output={"count": len(tasks)})
            )

            target_task = tasks[0] if tasks else None
            # Find specific task if mentioned
            for t in tasks:
                if any(word in t["title"].lower() for word in msg_lower.split() if len(word) > 3):
                    target_task = t
                    break

            if not target_task:
                return "I couldn't find an active task to reschedule. Please create a task first!", tool_traces

            res = self.runner.reschedule_task(target_task["id"])
            tool_traces.append(
                ToolCallTrace(tool_name="reschedule_task", arguments={"task_id": target_task["id"]}, output=res)
            )

            response = (
                f"📅 **Task Rescheduled Successfully**\n\n"
                f"- **Task:** {target_task['title']}\n"
                f"- **New Target Date:** {res['new_due_date']}\n\n"
                f"{res['message']}"
            )
            return response, tool_traces

        # 3. Query: "What should I work on today?" / "Plan my day"
        elif any(kw in msg_lower for kw in ["today", "plan my day", "what should i do", "what should i work on", "schedule"]):
            daily_plan = self.runner.generate_daily_plan()
            calendar_events = self.runner.get_calendar_events()

            tool_traces.append(
                ToolCallTrace(tool_name="generate_daily_plan", arguments={}, output=daily_plan)
            )
            tool_traces.append(
                ToolCallTrace(tool_name="get_calendar_events", arguments={}, output=calendar_events)
            )

            schedule_text = ""
            for item in daily_plan.get("schedule", []):
                if item["item_type"] == "EVENT":
                    schedule_text += f"- 📅 **{item['time']}** — {item['title']} *(Calendar Event)*\n"
                else:
                    schedule_text += f"- ⚡ **{item['time']}** — {item['title']} *(Task)*\n"

            response = (
                f"### Today's Prioritized Daily Plan\n\n"
                f"**Available Time:** {daily_plan['available_hours']} hours | "
                f"**Required Effort:** {daily_plan['required_task_hours']} hours\n\n"
                f"**Schedule Breakdown:**\n{schedule_text}\n"
                f"**Recommendation:**\n{daily_plan['recommendation']}"
            )
            return response, tool_traces

        # 4. Query: "What tasks are overdue?"
        elif "overdue" in msg_lower:
            overdue = self.runner.get_overdue_tasks()
            tool_traces.append(
                ToolCallTrace(tool_name="get_overdue_tasks", arguments={}, output=overdue)
            )

            if not overdue:
                response = "Great news! You currently have no overdue tasks. All deadlines are up to date."
            else:
                items = "\n".join([f"- ⚠️ **{t['title']}** (Due: {t['due_date']}, Priority: {t['priority']})" for t in overdue])
                response = f"You have **{len(overdue)} overdue task(s)** that require immediate attention:\n\n{items}\n\n*I recommend tackling these before starting new tasks.*"
            return response, tool_traces

        # 5. Query: "Break this task into smaller tasks"
        elif "break" in msg_lower or "subtask" in msg_lower or "decompose" in msg_lower:
            target = user_message.replace("Break", "").replace("break", "").replace("into smaller tasks", "").replace("subtasks", "").replace("this task", "").replace("task", "").strip(" :\"'")
            if not target:
                target = "AI Project Preparation"

            res = self.runner.breakdown_task(target)
            tool_traces.append(
                ToolCallTrace(tool_name="breakdown_task", arguments={"title_or_id": target}, output=res)
            )

            sub_items = "\n".join([f"  ├── {st}" for st in res["subtasks"]])
            response = (
                f"I've broken down **'{target}'** into actionable subtasks:\n\n"
                f"```text\n{target}\n{sub_items}\n```\n\n"
                f"These subtasks have been added to your task manager!"
            )
            return response, tool_traces

        # 6. Intent: Task Creation ("Create a high-priority task to prepare for my AI interview by Friday.")
        elif any(kw in msg_lower for kw in ["need to", "have to", "create", "add task", "prepare", "finish", "complete"]):
            priority = "HIGH" if "high" in msg_lower or "urgent" in msg_lower else ("LOW" if "low" in msg_lower else "MEDIUM")
            due_str = "friday" if "friday" in msg_lower else ("tomorrow" if "tomorrow" in msg_lower else "today")

            title = user_message.strip()
            for kw in ["create a high-priority task to ", "create a task to ", "create task ", "add task ", "i need to "]:
                if kw in msg_lower:
                    idx = msg_lower.find(kw)
                    if idx != -1:
                        title = user_message[idx + len(kw):].strip()
                        break

            for w in ["by friday", "by tomorrow", "make it high priority", "high priority", "urgent"]:
                if w in title.lower():
                    idx = title.lower().find(w)
                    title = (title[:idx] + title[idx + len(w):]).strip(" .")

            if not title:
                title = "Prepare for AI interview"

            res = self.runner.create_task(
                title=title,
                priority=priority,
                due_date=due_str,
                estimated_minutes=120 if "interview" in title.lower() or "prepare" in title.lower() else 60
            )

            tool_traces.append(
                ToolCallTrace(tool_name="create_task", arguments={"title": title, "priority": priority, "due_date": due_str}, output=res)
            )

            response = (
                f"### Task Created Successfully\n\n"
                f"```text\nTask:     {title}\nPriority: {priority}\nDue Date: {res['due_date']}\nStatus:   Pending\n```\n\n"
                f"I've calculated an internal priority score based on proximity and effort and updated your schedule."
            )
            return response, tool_traces

        # Fallback response
        else:
            tasks = self.runner.get_tasks()
            tool_traces.append(
                ToolCallTrace(tool_name="get_tasks", arguments={}, output={"count": len(tasks)})
            )
            pending_titles = [t["title"] for t in tasks if t["status"] == "PENDING"][:3]
            titles_str = ", ".join(pending_titles) if pending_titles else "No pending tasks"

            response = (
                f"I'm your **Personal Planning Agent**. Currently managing **{len(tasks)} tasks** "
                f"({titles_str}).\n\n"
                f"Try asking me:\n"
                f"- *'What should I work on today?'*\n"
                f"- *'Do I have enough time to finish my tasks today?'*\n"
                f"- *'Create a high-priority task to prepare for my AI interview by Friday.'*\n"
                f"- *'Move my task to tomorrow.'*\n"
                f"- *'What tasks are overdue?'*"
            )
            return response, tool_traces
