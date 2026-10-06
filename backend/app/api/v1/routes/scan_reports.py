"""
Privacy Eye — Scan Reports API Routes
Endpoints:
- POST   /api/v1/reports            — Create persistent Scan Report from completed live scan
- GET    /api/v1/reports            — List authenticated user's scan reports (paginated & filtered)
- GET    /api/v1/reports/{id}       — Retrieve full scan report forensic details
- GET    /api/v1/reports/{id}/face  — Download/stream representative captured face image
- GET    /api/v1/reports/{id}/jpg   — Download high-resolution single-page JPG report card
- GET    /api/v1/reports/{id}/pdf   — Download official multi-page A4 PDF evidence dossier
- DELETE /api/v1/reports/{id}       — Delete report and purge all associated storage artifacts
- GET    /api/v1/reports/admin/all  — Admin review of all system reports (role-protected)
"""
import base64
import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.core.security import get_current_user
from app.database.models import User, UserRole
from app.schemas.schemas import (
    ScanReportCreateRequest,
    ScanReportResponse,
    ScanReportListResponse,
    ScanReportSignalResponse,
    ScanReportTestResponse,
)
from app.services.scan_report_service import scan_report_service

router = APIRouter()


def _format_report_response(report) -> ScanReportResponse:
    """Helper to convert ORM ScanReport to ScanReportResponse schema."""
    signals_resp = [
        ScanReportSignalResponse(
            id=s.id,
            signal_name=s.signal_name,
            signal_value=s.signal_value,
            signal_status=s.signal_status,
            signal_explanation=s.signal_explanation,
            created_at=s.created_at,
        )
        for s in (report.signals or [])
    ]

    tests_resp = [
        ScanReportTestResponse(
            id=t.id,
            test_name=t.test_name,
            status=t.status,
            score=t.score,
            message=t.message,
            timestamp=t.timestamp,
        )
        for t in (report.tests or [])
    ]

    return ScanReportResponse(
        id=report.id,
        report_number=report.report_number,
        user_id=report.user_id,
        live_session_id=report.live_session_id,
        assessment=report.assessment,
        category_label=report.category_label,
        confidence=report.confidence,
        reliability=report.reliability,
        input_quality=report.input_quality,
        processing_location=report.processing_location,
        has_face_capture=report.has_face_capture,
        face_capture_available=bool(report.has_face_capture and report.face_capture_storage_key),
        jpg_available=bool(report.jpg_report_storage_key),
        pdf_available=bool(report.pdf_report_storage_key),
        report_status=report.report_status,
        model_name=report.model_name,
        model_version=report.model_version,
        preprocessing_version=report.preprocessing_version,
        fusion_version=report.fusion_version,
        calibration_version=report.calibration_version,
        target_face_id=report.target_face_id,
        faces_detected_count=report.faces_detected_count,
        explanation=report.explanation,
        why_reasons=report.why_reasons or [],
        signals=signals_resp,
        tests=tests_resp,
        raw_snapshot=report.raw_snapshot or {},
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


@router.post("", response_model=ScanReportResponse, status_code=status.HTTP_201_CREATED)
async def create_scan_report(
    payload: ScanReportCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates an authoritative persistent Scan Report from completed live camera analysis.
    Consumes the exact inference snapshot emitted by the core model.
    """
    if not payload.live_session_id:
        raise HTTPException(status_code=400, detail="live_session_id is required")

    snapshot = payload.inference_result or {}

    face_bytes = None
    if payload.save_face_capture and payload.representative_frame_base64:
        try:
            b64_str = payload.representative_frame_base64
            if "," in b64_str:
                b64_str = b64_str.split(",", 1)[1]
            face_bytes = base64.b64decode(b64_str)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 face frame: {str(e)}")

    try:
        report = await scan_report_service.create_scan_report(
            db=db,
            user=current_user,
            live_session_id=payload.live_session_id,
            inference_snapshot=snapshot,
            representative_frame_bytes=face_bytes,
            save_face_capture=payload.save_face_capture,
        )
        return _format_report_response(report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate scan report: {str(e)}")


@router.get("", response_model=ScanReportListResponse)
async def list_scan_reports(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    assessment: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists scan reports belonging to the authenticated user.
    """
    items, total = await scan_report_service.list_reports(
        db=db,
        user=current_user,
        page=page,
        per_page=per_page,
        assessment_filter=assessment,
        search_query=search,
    )

    pages = math.ceil(total / per_page) if total > 0 else 1
    return ScanReportListResponse(
        items=[_format_report_response(r) for r in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/admin/all", response_model=ScanReportListResponse)
async def admin_list_all_reports(
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Admin-only review of all scan reports across all accounts.
    """
    try:
        items, total = await scan_report_service.admin_list_reports(
            db=db,
            admin_user=current_user,
            page=page,
            per_page=per_page,
            search_query=search,
        )
        pages = math.ceil(total / per_page) if total > 0 else 1
        return ScanReportListResponse(
            items=[_format_report_response(r) for r in items],
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/{report_id}", response_model=ScanReportResponse)
async def get_scan_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves full details of a scan report with strict ownership verification.
    """
    try:
        report = await scan_report_service.get_report_by_id(
            db=db,
            user=current_user,
            report_id=report_id,
        )
        return _format_report_response(report)
    except ValueError:
        raise HTTPException(status_code=404, detail="Scan report not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Access denied: You do not own this report")


@router.get("/{report_id}/face")
async def download_report_face_capture(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Streams the representative face image evidence captured during the scan.
    """
    try:
        file_bytes, mime_type, filename = await scan_report_service.get_report_file(
            db=db,
            user=current_user,
            report_id=report_id,
            file_type="face",
        )
        return Response(
            content=file_bytes,
            media_type=mime_type,
            headers={"Content-Disposition": f'inline; filename="{filename}"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/{report_id}/jpg")
async def download_report_jpg(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Downloads high-resolution single-page JPG report card.
    """
    try:
        file_bytes, mime_type, filename = await scan_report_service.get_report_file(
            db=db,
            user=current_user,
            report_id=report_id,
            file_type="jpg",
        )
        return Response(
            content=file_bytes,
            media_type=mime_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError:
        raise HTTPException(status_code=403, detail="Access denied")


@router.get("/{report_id}/pdf")
async def download_report_pdf(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Downloads official multi-page A4 PDF evidence dossier.
    """
    try:
        file_bytes, mime_type, filename = await scan_report_service.get_report_file(
            db=db,
            user=current_user,
            report_id=report_id,
            file_type="pdf",
        )
        return Response(
            content=file_bytes,
            media_type=mime_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError:
        raise HTTPException(status_code=403, detail="Access denied")


@router.delete("/{report_id}", status_code=status.HTTP_200_OK)
async def delete_scan_report(
    report_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deletes report and purges face captures and documents from storage.
    """
    try:
        await scan_report_service.delete_report(
            db=db,
            user=current_user,
            report_id=report_id,
        )
        return {
            "status": "DELETED",
            "report_id": report_id,
            "message": "Report and associated face captures deleted successfully.",
        }
    except ValueError:
        raise HTTPException(status_code=404, detail="Report not found")
    except PermissionError:
        raise HTTPException(status_code=403, detail="Access denied")
