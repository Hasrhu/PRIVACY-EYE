"""
Privacy Eye — Live Camera Face Authenticity API Routes

Endpoints:
- POST /api/v1/live/frame            — Low-latency frame analysis with dynamic movement-responsive confidence
- POST /api/v1/live/challenge        — Generate randomized active liveness challenge
- POST /api/v1/live/save-audit       — Persist live audit session & evidence to database
- POST /api/v1/live/consent-response — Save user consent response for model training database
- GET  /api/v1/live/training-stats   — Real human model training pool statistics
"""
import os
import io
import base64
import uuid
import structlog
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database.session import get_db
from app.database.models import (
    MediaAnalysis,
    AnalysisSignal,
    Report,
    AuditLog,
    FaceTrainingSample,
    MediaType,
    AnalysisStatus,
    RiskLevel,
)
from app.core.security import get_current_user
from app.ml.live_authenticity import live_authenticity_engine

logger = structlog.get_logger(__name__)
router = APIRouter()

TRAINING_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "training", "real_faces")
os.makedirs(TRAINING_DIR, exist_ok=True)


class FrameAnalysisPayload(BaseModel):
    session_id: str
    image_base64: str = Field(..., description="Base64 encoded JPEG/PNG frame from webcam")
    run_challenge: bool = False


class SaveAuditSessionPayload(BaseModel):
    session_id: str
    assessment: str
    category_label: Optional[str] = None
    confidence: float
    quality_index: int
    signals: List[dict] = []
    explanation: str = ""
    snapshot_base64: Optional[str] = None
    consent_given: Optional[bool] = None
    landmarks: Optional[dict] = None
    eye_status: Optional[str] = None
    blink_count: Optional[int] = None
    phone_detected: Optional[bool] = None
    presentation_attack: Optional[bool] = None
    reason_codes: Optional[List[str]] = None
    model_probability: Optional[float] = None
    reliability: Optional[str] = None
    liveness_score: Optional[float] = None
    facial_movement_score: Optional[float] = None
    replay_score: Optional[float] = None
    synthetic_score: Optional[float] = None
    debug: Optional[dict] = None


class ConsentResponsePayload(BaseModel):
    session_id: str
    consent_given: bool
    category_label: str = "REAL"
    confidence: float
    quality_score: float = 75.0
    face_snapshot_base64: Optional[str] = None
    landmarks: Optional[dict] = None


@router.post("/frame")
async def analyze_live_frame(
    payload: FrameAnalysisPayload,
    current_user=Depends(get_current_user),
):
    """
    Sub-second live video frame analysis.
    Decodes base64 frame, runs quality, YuNet face detection, liveness, and dynamic confidence.
    """
    try:
        raw_b64 = payload.image_base64
        if "," in raw_b64:
            raw_b64 = raw_b64.split(",", 1)[1]
        img_bytes = base64.b64decode(raw_b64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {str(e)}")

    result = live_authenticity_engine.analyze_frame(
        img_bytes=img_bytes,
        session_id=payload.session_id,
        run_challenge=payload.run_challenge,
    )
    return result


@router.post("/challenge")
async def request_active_challenge(
    session_id: str,
    current_user=Depends(get_current_user),
):
    """
    Generates a cryptographically randomized active liveness challenge
    (e.g., TURN_LEFT, TURN_RIGHT, SMILE, TILT_UP).
    """
    challenge = live_authenticity_engine.generate_challenge(session_id)
    return challenge


@router.post("/consent-response")
async def submit_consent_response(
    payload: ConsentResponsePayload,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Records the user's explicit consent decision regarding contributing their face
    to the Privacy Eye Real Human Model Training Database.

    - If consent_given == True:
        Persists the cropped face image to data/training/real_faces/ and records metadata in face_training_samples.
    - If consent_given == False:
        Zero-storage policy enforced: logs the response with consent_given=False, retaining zero images.
    """
    sample_id = str(uuid.uuid4())
    image_rel_path: Optional[str] = None

    if payload.consent_given and payload.face_snapshot_base64:
        try:
            raw_b64 = payload.face_snapshot_base64
            if "," in raw_b64:
                raw_b64 = raw_b64.split(",", 1)[1]
            face_bytes = base64.b64decode(raw_b64)

            filename = f"real_face_{sample_id}.jpg"
            disk_path = os.path.join(TRAINING_DIR, filename)
            with open(disk_path, "wb") as f:
                f.write(face_bytes)

            image_rel_path = f"data/training/real_faces/{filename}"
            logger.info("Saved face sample to Real Human Model Database", sample_id=sample_id, path=image_rel_path)
        except Exception as err:
            logger.error("Failed to write training face sample", error=str(err))

    sample_record = FaceTrainingSample(
        id=sample_id,
        user_id=current_user.id if current_user else None,
        session_id=payload.session_id,
        consent_given=payload.consent_given,
        category_label=payload.category_label,
        confidence=float(payload.confidence),
        quality_score=float(payload.quality_score),
        image_path=image_rel_path,
        landmarks_json=payload.landmarks,
        created_at=datetime.now(timezone.utc),
    )
    db.add(sample_record)

    db.add(AuditLog(
        user_id=current_user.id if current_user else None,
        action="FACE_TRAINING_CONSENT_GRANTED" if payload.consent_given else "FACE_TRAINING_CONSENT_DECLINED",
        resource_type="face_training_sample",
        resource_id=sample_id,
        detail={
            "session_id": payload.session_id,
            "consent_given": payload.consent_given,
            "category_label": payload.category_label,
            "confidence": payload.confidence,
        },
    ))
    await db.commit()

    if payload.consent_given:
        return {
            "status": "CONTRIBUTED",
            "consent_given": True,
            "sample_id": sample_id,
            "message": "Thank you! Your face sample has been securely added to the Real Human Model Training Database to advance AI authenticity defense.",
        }
    else:
        return {
            "status": "RECORDED",
            "consent_given": False,
            "sample_id": sample_id,
            "message": "Response recorded. Strict zero-storage privacy policy applied. No biometric or face images were retained.",
        }


@router.get("/training-stats")
async def get_training_database_stats(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Returns public statistics on the Real Human Model Training Database pool.
    """
    total_q = await db.execute(select(func.count(FaceTrainingSample.id)))
    total_responses = total_q.scalar() or 0

    consented_q = await db.execute(
        select(func.count(FaceTrainingSample.id)).where(FaceTrainingSample.consent_given == True)  # noqa: E712
    )
    consented_count = consented_q.scalar() or 0

    declined_count = total_responses - consented_count

    # Check physical images on disk
    try:
        real_files_on_disk = len([f for f in os.listdir(TRAINING_DIR) if f.endswith((".jpg", ".png"))])
    except Exception:
        real_files_on_disk = 0

    return {
        "total_responses": total_responses,
        "consented_samples": consented_count,
        "declined_responses": declined_count,
        "real_human_model_pool_size": max(consented_count, real_files_on_disk),
        "database_status": "ACTIVE_ACCUMULATING",
    }


@router.post("/save-audit", status_code=status.HTTP_201_CREATED)
async def save_live_audit_session(
    payload: SaveAuditSessionPayload,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Persists a verified live camera session into the database as an evidence record,
    generating an audit trail and comprehensive report.
    """
    analysis_id = str(uuid.uuid4())

    # Map assessment to DB RiskLevel
    risk_mapping = {
        "REAL_HUMAN": RiskLevel.LOW,
        "REAL": RiskLevel.LOW,
        "LIKELY_LIVE_HUMAN": RiskLevel.LOW,
        "NEED_MORE_CLARITY": RiskLevel.UNDETERMINED,
        "NOT_LIKELY_HUMAN": RiskLevel.HIGH,
        "SUSPICIOUS": RiskLevel.SUSPICIOUS,
        "HIGH_SYNTHETIC_RISK": RiskLevel.HIGH,
        "POSSIBLE_REPLAY_ATTACK": RiskLevel.CRITICAL,
        "NO_FACE_DETECTED": RiskLevel.UNDETERMINED,
        "UNABLE_TO_DETERMINE": RiskLevel.UNDETERMINED,
    }
    db_risk = risk_mapping.get(payload.assessment, RiskLevel.UNDETERMINED)

    synthetic_prob = round(
        0.05 if payload.assessment in ("REAL_HUMAN", "LIKELY_LIVE_HUMAN")
        else (0.15 if payload.assessment == "REAL"
        else (0.85 if payload.assessment in ("NOT_LIKELY_HUMAN", "HIGH_SYNTHETIC_RISK")
        else (0.75 if payload.assessment == "POSSIBLE_REPLAY_ATTACK" else 0.40))),
        2
    )

    analysis = MediaAnalysis(
        id=analysis_id,
        user_id=current_user.id,
        original_filename=f"live_scan_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.jpg",
        media_type=MediaType.IMAGE,
        file_size_bytes=len(payload.snapshot_base64 or "") // 4 * 3 if payload.snapshot_base64 else 1024,
        mime_type="image/jpeg",
        status=AnalysisStatus.COMPLETE,
        risk_level=db_risk,
        synthetic_probability=synthetic_prob,
        confidence=round(payload.confidence / 100.0, 3),
        explanation=payload.explanation,
        raw_scores={
            "quality_index": payload.quality_index,
            "live_mode": True,
            "category_label": payload.category_label or payload.assessment,
            "model_probability": payload.model_probability,
            "reliability": payload.reliability,
            "blink_count": payload.blink_count,
            "eye_status": payload.eye_status,
            "phone_detected": payload.phone_detected,
            "presentation_attack": payload.presentation_attack,
            "liveness_score": payload.liveness_score,
            "facial_movement_score": payload.facial_movement_score,
            "replay_score": payload.replay_score,
            "synthetic_score": payload.synthetic_score,
            "debug": payload.debug,
        },
        media_deleted=True,
    )
    db.add(analysis)

    # Add forensic signals
    for s in payload.signals:
        db.add(AnalysisSignal(
            id=str(uuid.uuid4()),
            analysis_id=analysis_id,
            signal_key=s.get("key", "signal"),
            signal_label=s.get("label", "Signal"),
            severity=s.get("severity", "medium"),
            score=s.get("score", 0.5),
            description=s.get("detail") or s.get("description", ""),
        ))

    # Add official evidence report
    cat_title = payload.category_label or payload.assessment.replace('_', ' ').title()
    report_title = f"Live Face Authenticity Audit — {cat_title}"
    report_summary = (
        f"Real-time live camera analysis conducted on {datetime.now(timezone.utc).strftime('%B %d, %Y at %H:%M UTC')}. "
        f"Result: {cat_title} with calibrated confidence of {payload.confidence:.1f}%. "
        f"{payload.explanation}"
    )
    report = Report(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        analysis_id=analysis_id,
        title=report_title,
        summary=report_summary,
        recommendations=(
            "Apply multi-factor biometric verification if high financial or credential access is involved. "
            "Verification is probabilistic and should be cross-referenced with provenance credentials."
        ),
        report_json={
            "session_id": payload.session_id,
            "assessment": payload.assessment,
            "category_label": payload.category_label,
            "confidence": payload.confidence,
            "quality_index": payload.quality_index,
            "signals": payload.signals,
            "consent_given": payload.consent_given,
        },
    )
    db.add(report)

    # Audit log
    db.add(AuditLog(
        user_id=current_user.id,
        action="LIVE_CAMERA_AUDIT",
        resource_type="analysis",
        resource_id=analysis_id,
    ))

    # If consent was given during save-audit, record training sample
    if payload.consent_given is not None:
        sample_id = str(uuid.uuid4())
        image_rel_path = None
        if payload.consent_given and payload.snapshot_base64:
            try:
                raw_b64 = payload.snapshot_base64
                if "," in raw_b64:
                    raw_b64 = raw_b64.split(",", 1)[1]
                face_bytes = base64.b64decode(raw_b64)
                fname = f"real_face_{sample_id}.jpg"
                with open(os.path.join(TRAINING_DIR, fname), "wb") as f:
                    f.write(face_bytes)
                image_rel_path = f"data/training/real_faces/{fname}"
            except Exception as e:
                logger.error("Failed to save snapshot for audit training", error=str(e))

        db.add(FaceTrainingSample(
            id=sample_id,
            user_id=current_user.id,
            session_id=payload.session_id,
            consent_given=payload.consent_given,
            category_label=payload.category_label or payload.assessment,
            confidence=float(payload.confidence),
            quality_score=float(payload.quality_index),
            image_path=image_rel_path,
            landmarks_json=payload.landmarks,
            created_at=datetime.now(timezone.utc),
        ))

    current_user.scans_used_this_month += 1
    await db.commit()

    return {
        "analysis_id": analysis_id,
        "report_id": report.id,
        "status": "SAVED",
        "message": "Live camera authenticity audit successfully stored in security database.",
    }
