"""
Users routes — profile management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.schemas.schemas import UserResponse
from app.core.security import get_current_user

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_profile(current_user=Depends(get_current_user)):
    """Get current user profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_profile(
    full_name: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update display name."""
    current_user.full_name = full_name[:200]
    await db.flush()
    return current_user
