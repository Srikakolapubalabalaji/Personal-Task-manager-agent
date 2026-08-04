from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class CalendarEvent(BaseModel):
    id: str
    summary: str
    description: Optional[str] = None
    start: datetime
    end: datetime
    location: Optional[str] = None
    is_all_day: bool = False


class CalendarEventCreate(BaseModel):
    summary: str
    description: Optional[str] = None
    start: datetime
    end: datetime
    location: Optional[str] = None


class AvailableTimeSlot(BaseModel):
    start: datetime
    end: datetime
    duration_minutes: int


class GoogleAuthUrlResponse(BaseModel):
    auth_url: str


class CalendarStatusResponse(BaseModel):
    connected: bool
    provider: str = "google"
    account_email: Optional[str] = None
