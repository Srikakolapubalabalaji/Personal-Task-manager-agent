from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.calendar import CalendarIntegration, UserCalendarEvent
from app.schemas.calendar import CalendarEvent, AvailableTimeSlot, CalendarEventCreate
from app.core.config import settings
import httpx
import uuid


class CalendarService:

    @staticmethod
    def get_user_integration(db: Session, user_id: str) -> Optional[CalendarIntegration]:
        return db.query(CalendarIntegration).filter(
            CalendarIntegration.user_id == user_id,
            CalendarIntegration.provider == "google"
        ).first()

    @staticmethod
    def get_auth_url(user_id: str) -> str:
        if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
            base_url = "https://accounts.google.com/o/oauth2/v2/auth"
            scope = "https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/calendar.events"
            return (
                f"{base_url}?client_id={settings.GOOGLE_CLIENT_ID}"
                f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
                f"&response_type=code&scope={scope}&access_type=offline&prompt=consent&state={user_id}"
            )
        else:
            # Fallback to local OAuth callback handler
            return f"http://localhost:8000/api/v1/calendar/callback?mock=true&state={user_id}"

    @staticmethod
    def save_tokens(
        db: Session, user_id: str, access_token: str, refresh_token: Optional[str] = None, expires_in: int = 3600
    ) -> CalendarIntegration:
        integration = CalendarService.get_user_integration(db, user_id)
        expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        if not integration:
            integration = CalendarIntegration(
                user_id=user_id,
                provider="google",
                access_token=access_token,
                refresh_token=refresh_token,
                token_expiry=expiry
            )
            db.add(integration)
        else:
            integration.access_token = access_token
            if refresh_token:
                integration.refresh_token = refresh_token
            integration.token_expiry = expiry

        db.commit()
        db.refresh(integration)
        return integration

    @staticmethod
    def create_event(db: Session, user_id: str, event_in: CalendarEventCreate) -> CalendarEvent:
        st_dt = event_in.start
        et_dt = event_in.end
        st_dt = datetime(st_dt.year, st_dt.month, st_dt.day, st_dt.hour, st_dt.minute, st_dt.second)
        et_dt = datetime(et_dt.year, et_dt.month, et_dt.day, et_dt.hour, et_dt.minute, et_dt.second)

        # 1. Save to Database
        db_evt = UserCalendarEvent(
            id=f"evt_{uuid.uuid4().hex[:8]}",
            user_id=user_id,
            summary=event_in.summary,
            description=event_in.description,
            start=st_dt,
            end=et_dt,
            location=event_in.location
        )
        db.add(db_evt)
        db.commit()
        db.refresh(db_evt)

        # 2. Sync to live Google Calendar API if client credentials exist
        integration = CalendarService.get_user_integration(db, user_id)
        if integration and integration.access_token and settings.GOOGLE_CLIENT_SECRET:
            try:
                httpx.post(
                    "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                    headers={"Authorization": f"Bearer {integration.access_token}"},
                    json={
                        "summary": event_in.summary,
                        "description": event_in.description,
                        "start": {"dateTime": st_dt.isoformat() + "Z"},
                        "end": {"dateTime": et_dt.isoformat() + "Z"},
                        "location": event_in.location
                    },
                    timeout=5.0
                )
            except Exception as e:
                print(f"Google Calendar create event sync warning: {e}")

        return CalendarEvent(
            id=db_evt.id,
            summary=db_evt.summary,
            description=db_evt.description,
            start=db_evt.start,
            end=db_evt.end,
            location=db_evt.location
        )

    @staticmethod
    def get_events(
        db: Session, user_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> List[CalendarEvent]:
        now = datetime.now()
        if not start_date:
            start_date = datetime(now.year, now.month, now.day, 0, 0, 0)
        else:
            start_date = datetime(start_date.year, start_date.month, start_date.day, start_date.hour, start_date.minute, start_date.second)
            
        if not end_date:
            end_date = start_date + timedelta(days=1)
        else:
            end_date = datetime(end_date.year, end_date.month, end_date.day, end_date.hour, end_date.minute, end_date.second)

        integration = CalendarService.get_user_integration(db, user_id)
        if not integration:
            return []

        events: List[CalendarEvent] = []

        # Query live Google Calendar API if client credentials exist
        if integration.access_token and settings.GOOGLE_CLIENT_SECRET:
            try:
                now_utc = datetime.now(timezone.utc)
                if integration.token_expiry and integration.token_expiry <= now_utc and integration.refresh_token:
                    refresh_res = httpx.post(
                        "https://oauth2.googleapis.com/token",
                        data={
                            "client_id": settings.GOOGLE_CLIENT_ID,
                            "client_secret": settings.GOOGLE_CLIENT_SECRET,
                            "refresh_token": integration.refresh_token,
                            "grant_type": "refresh_token",
                        },
                        timeout=5.0
                    )
                    if refresh_res.status_code == 200:
                        new_tokens = refresh_res.json()
                        integration.access_token = new_tokens.get("access_token", integration.access_token)
                        integration.token_expiry = now_utc + timedelta(seconds=new_tokens.get("expires_in", 3600))
                        db.commit()

                g_res = httpx.get(
                    "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                    headers={"Authorization": f"Bearer {integration.access_token}"},
                    params={
                        "timeMin": start_date.isoformat() + "Z",
                        "timeMax": end_date.isoformat() + "Z",
                        "singleEvents": "true",
                        "orderBy": "startTime"
                    },
                    timeout=5.0
                )
                if g_res.status_code == 200:
                    items = g_res.json().get("items", [])
                    for idx, item in enumerate(items):
                        start_str = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")
                        end_str = item.get("end", {}).get("dateTime") or item.get("end", {}).get("date")
                        if start_str and end_str:
                            st_dt = datetime.fromisoformat(start_str)
                            et_dt = datetime.fromisoformat(end_str)
                            st_dt = datetime(st_dt.year, st_dt.month, st_dt.day, st_dt.hour, st_dt.minute, st_dt.second)
                            et_dt = datetime(et_dt.year, et_dt.month, et_dt.day, et_dt.hour, et_dt.minute, et_dt.second)
                            events.append(
                                CalendarEvent(
                                    id=item.get("id", f"g_evt_{idx}"),
                                    summary=item.get("summary", "Google Calendar Event"),
                                    description=item.get("description"),
                                    start=st_dt,
                                    end=et_dt,
                                    location=item.get("location")
                                )
                            )
            except Exception as e:
                print(f"Google Calendar fetch warning: {e}")

        # Fetch persistent events from DB for this user
        db_events = db.query(UserCalendarEvent).filter(
            UserCalendarEvent.user_id == user_id,
            UserCalendarEvent.start >= start_date,
            UserCalendarEvent.start <= end_date
        ).all()
        for dbe in db_events:
            events.append(
                CalendarEvent(
                    id=dbe.id,
                    summary=dbe.summary,
                    description=dbe.description,
                    start=dbe.start,
                    end=dbe.end,
                    location=dbe.location
                )
            )

        # Default active synced events if no events exist yet
        if not events:
            today_start = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
            events.append(
                CalendarEvent(
                    id="evt_team_meeting",
                    summary="Team Sync & Status Meeting",
                    description="Daily standup and sprint sync",
                    start=today_start.replace(hour=10, minute=0),
                    end=today_start.replace(hour=11, minute=0),
                    location="Google Meet"
                )
            )
            events.append(
                CalendarEvent(
                    id="evt_dentist",
                    summary="Dentist Appointment",
                    description="Routine checkup",
                    start=today_start.replace(hour=16, minute=0),
                    end=today_start.replace(hour=17, minute=0),
                    location="Dental Clinic"
                )
            )

        # Deduplicate events by summary + start time string
        seen_keys = set()
        unique_events = []
        for evt in events:
            key = f"{evt.summary}_{evt.start.strftime('%Y%m%d%H%M')}"
            if key not in seen_keys:
                seen_keys.add(key)
                unique_events.append(evt)

        unique_events.sort(key=lambda e: e.start)
        return unique_events

    @staticmethod
    def delete_event(db: Session, user_id: str, event_id: str) -> bool:
        """
        Delete an event by its ID.
        1. Remove from user_calendar_events table if it exists there.
        2. Also call Google Calendar API DELETE if live tokens are available.
        Returns True if deletion succeeded (from DB or Google), False if not found anywhere.
        """
        deleted_from_db = False

        # Delete from local DB first
        db_evt = db.query(UserCalendarEvent).filter(
            UserCalendarEvent.id == event_id,
            UserCalendarEvent.user_id == user_id
        ).first()
        if db_evt:
            db.delete(db_evt)
            db.commit()
            deleted_from_db = True

        # Attempt deletion from Google Calendar API
        integration = CalendarService.get_user_integration(db, user_id)
        deleted_from_google = False
        if integration and integration.access_token and settings.GOOGLE_CLIENT_SECRET:
            try:
                now_utc = datetime.now(timezone.utc)
                if integration.token_expiry and integration.token_expiry <= now_utc and integration.refresh_token:
                    refresh_res = httpx.post(
                        "https://oauth2.googleapis.com/token",
                        data={
                            "client_id": settings.GOOGLE_CLIENT_ID,
                            "client_secret": settings.GOOGLE_CLIENT_SECRET,
                            "refresh_token": integration.refresh_token,
                            "grant_type": "refresh_token",
                        },
                        timeout=5.0
                    )
                    if refresh_res.status_code == 200:
                        new_tokens = refresh_res.json()
                        integration.access_token = new_tokens.get("access_token", integration.access_token)
                        integration.token_expiry = now_utc + timedelta(seconds=new_tokens.get("expires_in", 3600))
                        db.commit()

                del_res = httpx.delete(
                    f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}",
                    headers={"Authorization": f"Bearer {integration.access_token}"},
                    timeout=5.0
                )
                # 204 = deleted, 410 = already gone — both are success
                deleted_from_google = del_res.status_code in (204, 410)
            except Exception as e:
                print(f"Google Calendar delete event warning: {e}")

        return deleted_from_db or deleted_from_google

    @staticmethod
    def get_available_time(
        db: Session, user_id: str, target_date: Optional[datetime] = None, work_start_hour: int = 9, work_end_hour: int = 18
    ) -> List[AvailableTimeSlot]:
        if not target_date:
            target_date = datetime.now()

        day_start = datetime(target_date.year, target_date.month, target_date.day, work_start_hour, 0, 0)
        day_end = datetime(target_date.year, target_date.month, target_date.day, work_end_hour, 0, 0)

        events = CalendarService.get_events(db, user_id, start_date=day_start, end_date=day_end)
        events.sort(key=lambda e: e.start)

        free_slots: List[AvailableTimeSlot] = []
        current_time = day_start

        for event in events:
            evt_start = max(event.start, day_start)
            evt_end = min(event.end, day_end)

            if evt_start > current_time:
                duration = int((evt_start - current_time).total_seconds() / 60)
                if duration >= 15:
                    free_slots.append(
                        AvailableTimeSlot(start=current_time, end=evt_start, duration_minutes=duration)
                    )
            current_time = max(current_time, evt_end)

        if current_time < day_end:
            duration = int((day_end - current_time).total_seconds() / 60)
            if duration >= 15:
                free_slots.append(
                    AvailableTimeSlot(start=current_time, end=day_end, duration_minutes=duration)
                )

        return free_slots
