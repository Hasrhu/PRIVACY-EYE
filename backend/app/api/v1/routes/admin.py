"""
Admin routes — system monitoring (Admin role required).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.session import get_db
from app.database.models import User, MediaAnalysis, ModelVersion, UserRole
from app.schemas.schemas import ModelVersionResponse
from app.core.security import get_current_user
from typing import List

router = APIRouter()


async def require_admin(current_user=Depends(get_current_user)):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/stats")
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """System-wide statistics for admin dashboard."""
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar()
    total_scans = (await db.execute(select(func.count()).select_from(MediaAnalysis))).scalar()

    return {
        "total_users": total_users,
        "total_scans": total_scans,
    }


@router.get("/models", response_model=List[ModelVersionResponse])
async def list_models(
    db: AsyncSession = Depends(get_db),
    admin=Depends(require_admin),
):
    """List all registered ML model versions."""
    result = await db.execute(select(ModelVersion).order_by(ModelVersion.created_at.desc()))
    return result.scalars().all()


@router.get("/model/current")
async def current_model_version():
    """Get currently active model version info (public endpoint for auditability)."""
    from app.services.ml_service import ml_service
    return ml_service.get_model_info()
