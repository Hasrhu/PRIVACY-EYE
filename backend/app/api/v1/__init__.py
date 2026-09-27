"""
API v1 Router — aggregates all route modules.
"""
from fastapi import APIRouter
from app.api.v1.routes import auth, analysis, reports, users, admin, live_scan

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(analysis.router, prefix="/analyze", tags=["Analysis"])
router.include_router(live_scan.router, prefix="/live", tags=["Live Camera"])
router.include_router(reports.router, prefix="/reports", tags=["Reports"])
router.include_router(admin.router, prefix="/admin", tags=["Admin"])
