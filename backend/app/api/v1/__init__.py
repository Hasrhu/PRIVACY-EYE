"""
API v1 Router — aggregates all route modules.
"""
from fastapi import APIRouter
from app.api.v1.routes import auth, analysis, reports, scan_reports, users, admin, live_scan, dataset

router = APIRouter()
router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
router.include_router(users.router, prefix="/users", tags=["Users"])
router.include_router(analysis.router, prefix="/analyze", tags=["Analysis"])
router.include_router(live_scan.router, prefix="/live", tags=["Live Camera"])
router.include_router(dataset.router, tags=["Dataset & Governance"])
router.include_router(reports.router, prefix="/reports", tags=["Reports"])
router.include_router(scan_reports.router, prefix="/scan-reports", tags=["Scan Reports"])
router.include_router(admin.router, prefix="/admin", tags=["Admin"])
