from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
import httpx
import urllib.parse
from app.database.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token, UserLogin
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.config import settings
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/google/url")
def get_google_oauth_url():
    if not settings.GOOGLE_CLIENT_ID:
        return {"auth_url": f"{settings.FRONTEND_URL}/login?mock_oauth=true"}
    
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    url = f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"
    return {"auth_url": url}


@router.get("/google/callback")
async def google_oauth_callback(
    code: Optional[str] = None,
    error: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if error or not code:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=oauth_failed")

    if not settings.GOOGLE_CLIENT_SECRET or not settings.GOOGLE_CLIENT_ID:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=missing_credentials")

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
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=token_exchange_failed")
        
        tokens = res.json()
        access_token_google = tokens.get("access_token")
        
        # Get user info from Google
        userinfo_res = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token_google}"}
        )
        if userinfo_res.status_code != 200:
            return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=userinfo_failed")
        
        user_info = userinfo_res.json()
        email = user_info.get("email")
        name = user_info.get("name", email.split("@")[0] if email else "Google User")

    if not email:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?error=email_missing")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            hashed_password=get_password_hash("oauth_google_protected_pass_123!"),
            full_name=name,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    jwt_token = create_access_token(subject=user.id)
    return RedirectResponse(url=f"{settings.FRONTEND_URL}/login?token={jwt_token}")


@router.post("/google/mock", response_model=Token)
def google_mock_auth(db: Session = Depends(get_db)):
    """
    Mock OAuth login endpoint for testing and local development.
    """
    mock_email = "alex.google@taskagent.ai"
    user = db.query(User).filter(User.email == mock_email).first()
    if not user:
        user = User(
            email=mock_email,
            hashed_password=get_password_hash("oauth_mock_pass_123!"),
            full_name="Alex Morgan (Google OAuth)",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token, user=UserResponse.model_validate(user))

