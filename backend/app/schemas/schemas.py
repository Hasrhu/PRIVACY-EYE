"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=200)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    role: str
    is_verified: bool
    scans_used_this_month: int
    scans_limit: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Analysis ──────────────────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    LOW = "LOW"
    SUSPICIOUS = "SUSPICIOUS"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNDETERMINED = "UNDETERMINED"


class AnalysisStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class SignalResponse(BaseModel):
    signal_key: str
    signal_label: str
    severity: str
    score: Optional[float]
    description: Optional[str]

    model_config = {"from_attributes": True}


class AnalysisResponse(BaseModel):
    id: str
    original_filename: str
    media_type: str
    file_size_bytes: int
    file_sha256: Optional[str]
    mime_type: Optional[str]
    duration_seconds: Optional[float]
    status: str
    risk_level: Optional[str]
    synthetic_probability: Optional[float]
    confidence: Optional[float]
    explanation: Optional[str]
    signals: List[SignalResponse] = []
    raw_scores: Optional[Dict[str, Any]]
    provenance_info: Optional[Dict[str, Any]]
    media_deleted: bool
    processing_ms: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnalysisListResponse(BaseModel):
    items: List[AnalysisResponse]
    total: int
    page: int
    per_page: int


# ── Reports ───────────────────────────────────────────────────────────────────

class ReportResponse(BaseModel):
    id: str
    analysis_id: str
    title: str
    summary: Optional[str]
    recommendations: Optional[str]
    report_json: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Model Version ─────────────────────────────────────────────────────────────

class ModelVersionResponse(BaseModel):
    id: str
    name: str
    version: str
    model_type: str
    description: Optional[str]
    accuracy: Optional[float]
    f1_score: Optional[float]
    roc_auc: Optional[float]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Dashboard Stats ───────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_scanned: int
    suspicious: int
    low_risk: int
    high_risk: int
    critical: int
    undetermined: int
    scans_this_month: int
    scans_limit: int
