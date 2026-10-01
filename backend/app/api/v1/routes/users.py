"""
Privacy Eye — User Profile & Account Management Routes
Endpoints:
- GET    /api/v1/users/me — Get authenticated user profile
- PATCH  /api/v1/users/me — Update profile details
- DELETE /api/v1/users/me — Permanently delete account with cascade
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.database.session import get_db
from app.database.models import User, AuditLog
from app.schemas.schemas import UserResponse, DeleteAccountRequest
from app.core.security import get_current_user
from app.services.user_service import user_service

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Retrieve profile of the currently authenticated user."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    full_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update user full name."""
    clean_name = full_name.strip()[:200]
    if not clean_name:
        raise HTTPException(status_code=400, detail="Name cannot be empty.")
    current_user.full_name = clean_name
    await db.commit()
    return current_user


@router.delete("/me")
async def delete_account(
    body: DeleteAccountRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Permanently delete the authenticated user account and all owned assets
    (analyses, signals, reports, sessions). Requires password confirmation.
    """
    user_id = current_user.id
    email = current_user.email

    deleted = await user_service.delete_account(db, current_user, body.password_confirmation)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password confirmation failed. Account was not deleted.",
        )

    db.add(AuditLog(
        user_id=None,
        action="ACCOUNT_DELETED",
        detail={"user_id": user_id, "email": email},
    ))
    await db.commit()
    logger.info("Account permanently deleted", user_id=user_id)

    return {
        "success": True,
        "message": "Your account and all associated data have been permanently deleted.",
    }
