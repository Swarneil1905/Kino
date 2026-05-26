import os
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db, rating_count
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.user import GoogleAuthIn, LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
async def register(payload: RegisterIn, db: Annotated[AsyncSession, Depends(get_db)]) -> TokenOut:
    existing = await db.execute(select(User).where(User.email == payload.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        auth_provider="email",
        is_admin=payload.email == settings.admin_email,
        last_login_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return TokenOut(access_token=create_access_token(user.id), user_id=str(user.id))


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, db: Annotated[AsyncSession, Depends(get_db)]) -> TokenOut:
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash or ""):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    return TokenOut(access_token=create_access_token(user.id), user_id=str(user.id))


@router.post("/google", response_model=TokenOut)
async def google_auth(payload: GoogleAuthIn, db: Annotated[AsyncSession, Depends(get_db)]) -> TokenOut:
    """Verify a Google ID token issued by NextAuth and return a Kino JWT."""
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    if not client_id:
        raise HTTPException(status_code=500, detail="Google OAuth not configured on server")

    try:
        id_info = google_id_token.verify_oauth2_token(
            payload.id_token,
            google_requests.Request(),
            client_id,
        )
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")

    google_id = id_info["sub"]
    email = id_info["email"]

    # Find by google_id first, then fall back to email to link existing accounts
    result = await db.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if user is None:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=email,
            google_id=google_id,
            auth_provider="google",
            is_admin=email == settings.admin_email,
        )
        db.add(user)
    else:
        if user.google_id is None:
            user.google_id = google_id
            user.auth_provider = "google"
        if email == settings.admin_email:
            user.is_admin = True

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(user)

    return TokenOut(access_token=create_access_token(user.id), user_id=str(user.id))


@router.get("/me", response_model=UserOut)
async def me(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserOut:
    count = await rating_count(db, user.id)
    return UserOut(
        id=str(user.id),
        email=user.email,
        created_at=user.created_at,
        rating_count=count,
        is_admin=user.is_admin,
        auth_provider=user.auth_provider,
    )
