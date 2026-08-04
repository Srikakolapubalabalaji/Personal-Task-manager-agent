# Personal Task Manager Agent — Production Documentation

A production-ready **Personal Task Manager Agent** that combines task management with **Google Calendar integration** and an **AI-powered planning agent**.

---

## 1. Project Overview & Objectives
The core purpose of this application is an intelligent agent that understands the user's tasks, deadlines, urgency, priorities, calendar events, available time, and contextual instructions, and then generates a **prioritized, realistic daily & weekly plan**.

---

## 2. Key Features
- **Task Management**: Full CRUD, status toggling, priorities (High, Medium, Low), estimated effort (minutes), category tags, due dates, subtasks, and automated AI task breakdown.
- **Google Calendar OAuth 2.0 Integration**: Syncs calendar events, detects busy meeting blocks, computes free focus windows, and prevents scheduling work during calendar appointments.
- **Algorithmic Priority Score Engine**:
  $$\text{Priority Score} = \text{UrgencyScore} + \text{ImportanceScore} + \text{OverdueBoost} + \text{DurationFit}$$
- **Daily & Weekly Interval Planning**: Packs tasks chronologically into free focus windows, detects schedule overload, and generates actionable rescheduling advice.
- **LangGraph AI Agent Assistant**: Stateful agent router supporting 15+ tool calls (`generate_daily_plan`, `create_task`, `breakdown_task`, `get_calendar_events`, `reschedule_task`).
- **Modern Dark Glassmorphic Dashboard**: Next.js 14 App Router, Tailwind CSS, Lucide icons, interactive statistics widgets, schedule timeline visualizer, and slide-over AI chat drawer.

---

## 3. System Architecture

```
User -> Next.js Frontend (App Router, Tailwind CSS)
            |
            v  REST API (JWT Bearer Token)
     FastAPI Async Backend
       |       |       |
       |       |       +---> Google Calendar API (OAuth 2.0)
       |       +-----------> LangGraph AI Planning Agent & Tools
       v
  SQLAlchemy 2.0 (PostgreSQL / SQLite)
```

---

## 4. Database Schema (PostgreSQL)

### Users (`users`)
- `id` (UUID, Primary Key)
- `email` (String, Unique)
- `hashed_password` (String)
- `full_name` (String)
- `created_at`, `updated_at` (DateTime)

### Tasks (`tasks`)
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key -> `users.id`)
- `title` (String), `description` (Text)
- `status` (Enum: `PENDING`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`)
- `priority` (Enum: `HIGH`, `MEDIUM`, `LOW`)
- `due_date` (DateTime)
- `estimated_minutes` (Integer)
- `category` (String)
- `priority_score` (Float)
- `created_at`, `updated_at`, `completed_at` (DateTime)

### Subtasks (`subtasks`)
- `id` (UUID, Primary Key)
- `task_id` (UUID, Foreign Key -> `tasks.id`)
- `title` (String)
- `status` (Enum: `PENDING`, `COMPLETED`)

### Calendar Integration (`calendar_integrations`)
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key -> `users.id`)
- `provider` (String)
- `access_token` (Text)
- `refresh_token` (Text)
- `token_expiry` (DateTime)

---

## 5. API Endpoints Reference

### Authentication
- `POST /api/v1/auth/register` — Register a new user and receive JWT.
- `POST /api/v1/auth/login` — Login with credentials and receive JWT.
- `GET  /api/v1/auth/me` — Retrieve current authenticated user profile.

### Tasks & Subtasks
- `GET    /api/v1/tasks` — List tasks with optional status & category filter.
- `POST   /api/v1/tasks` — Create task with optional due date & subtasks.
- `GET    /api/v1/tasks/{id}` — Get task details by ID.
- `PUT    /api/v1/tasks/{id}` — Update task properties.
- `DELETE /api/v1/tasks/{id}` — Delete task.
- `POST   /api/v1/tasks/{id}/complete` — Mark task as completed.
- `POST   /api/v1/tasks/{id}/breakdown` — Intelligently decompose task into AI subtasks.

### Google Calendar
- `GET  /api/v1/calendar/auth-url` — Get Google OAuth 2.0 authorization URL.
- `GET  /api/v1/calendar/status` — Get calendar connection status.
- `POST /api/v1/calendar/connect-mock` — Connect mock calendar for local demo.
- `GET  /api/v1/calendar/events` — Retrieve upcoming calendar events.
- `GET  /api/v1/calendar/availability` — Compute free focus time slots.

### Planner & Agent
- `GET  /api/v1/planner/today` — Generate prioritized daily plan and overload diagnosis.
- `GET  /api/v1/planner/week` — Generate 5-day work plan summary.
- `POST /api/v1/planner/reschedule` — Reschedule a task to a new target date.
- `POST /api/v1/agent/chat` — Interact with conversational AI Agent.

---

## 6. Local Setup & Execution Guide

### Prerequisites
- Python 3.11+
- Node.js 18+
- (Optional) Docker & Docker Compose

### Step 1: Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API Documentation will be served at `http://localhost:8000/api/v1/docs`.

### Step 2: Running Pytest Test Suite
```bash
cd backend
pytest
```

### Step 3: Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your web browser.

---

## 7. Docker Deployment
Run the complete stack (PostgreSQL + FastAPI + Next.js) using Docker Compose:
```bash
docker-compose up --build
```
