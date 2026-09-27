"""
Auth routes: register, login, refresh, logout.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.database.session import get_db
from app.schemas.schemas import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token, get_current_user
from app.services.user_service import user_service
from app.database.models import AuditLog
import structlog

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    existing = await user_service.get_by_email(db, body.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await user_service.create(db, body)
    logger.info("User registered", user_id=user.id)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    user = await user_service.get_by_email(db, body.email)
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account deactivated")

    # Update last login
    user.last_login_at = datetime.now(timezone.utc)
    await db.flush()

    # Audit
    db.add(AuditLog(
        user_id=user.id, action="LOGIN",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    ))

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    from app.core.config import settings
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(refresh_token: str, db: AsyncSession = Depends(get_db)):
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = await user_service.get_by_id(db, payload["sub"])
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")

    from app.core.config import settings
    access_token = create_access_token(user.id)
    new_refresh = create_refresh_token(user.id)
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user=Depends(get_current_user)):
    return current_user
