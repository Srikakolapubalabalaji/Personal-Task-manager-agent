from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import httpx
from datetime import datetime, timezone
from app.database.session import get_db
from app.models.user import User
from app.schemas.calendar import (
    CalendarEvent,
    CalendarEventCreate,
    AvailableTimeSlot,
    GoogleAuthUrlResponse,
    CalendarStatusResponse,
)
from app.services.calendar_service import CalendarService
from app.core.config import settings
from app.api.deps import get_current_user

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/auth-url", response_model=GoogleAuthUrlResponse)
def get_auth_url(current_user: User = Depends(get_current_user)):
    url = CalendarService.get_auth_url(current_user.id)
    return GoogleAuthUrlResponse(auth_url=url)


@router.get("/callback")
async def google_oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    mock: Optional[bool] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Handles Google OAuth 2.0 redirect, exchanges authorization code for tokens,
    and persists access & refresh tokens securely in PostgreSQL/SQLite DB.
    """
    if error:
        return RedirectResponse(url="http://localhost:3000/calendar?error=" + error)

    user_id = state
    if not user_id:
        return RedirectResponse(url="http://localhost:3000/calendar?error=invalid_state")

    if mock or not settings.GOOGLE_CLIENT_SECRET:
        # Save mock integration for testing
        CalendarService.save_tokens(
            db, user_id, access_token="mock_google_access_token", refresh_token="mock_google_refresh_token"
        )
        return RedirectResponse(url="http://localhost:3000/calendar?connected=true")

    # Exchange code for token with Google Token Endpoint
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        res = await client.post(token_url, data=data)
        if res.status_code != 200:
            return RedirectResponse(url="http://localhost:3000/calendar?error=token_exchange_failed")
        tokens = res.json()

    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    expires_in = tokens.get("expires_in", 3600)

    CalendarService.save_tokens(db, user_id, access_token, refresh_token, expires_in)
    return RedirectResponse(url="http://localhost:3000/calendar?connected=true")


@router.get("/status", response_model=CalendarStatusResponse)
def get_calendar_status(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    integration = CalendarService.get_user_integration(db, current_user.id)
    connected = integration is not None
    return CalendarStatusResponse(
        connected=connected,
        provider="google",
        account_email=current_user.email if connected else None
    )


@router.post("/connect-mock", response_model=CalendarStatusResponse)
def connect_mock_calendar(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    CalendarService.save_tokens(
        db, current_user.id, access_token="mock_access_token_xyz", refresh_token="mock_refresh_token_abc"
    )
    return CalendarStatusResponse(
        connected=True,
        provider="google",
        account_email=current_user.email
    )


@router.get("/events", response_model=List[CalendarEvent])
def get_events(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CalendarService.get_events(db, current_user.id, start_date=start_date, end_date=end_date)


@router.post("/events", response_model=CalendarEvent)
def create_event(
    req: CalendarEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CalendarService.create_event(db, current_user.id, req)


@router.delete("/events/{event_id}", status_code=204)
def delete_event(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = CalendarService.delete_event(db, current_user.id, event_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Event not found or could not be deleted")


@router.get("/availability", response_model=List[AvailableTimeSlot])
def get_availability(
    target_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return CalendarService.get_available_time(db, current_user.id, target_date=target_date)
