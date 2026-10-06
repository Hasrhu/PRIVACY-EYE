"""
Privacy Eye — Centralized Eye Tracking & Blink Detection Configuration
All parameters governing ocular localization, quality gating, temporal state machine,
and event generation are declared here.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any


class EyeVisibilityState(str, Enum):
    BOTH_VISIBLE = "BOTH_VISIBLE"
    LEFT_ONLY = "LEFT_ONLY"
    RIGHT_ONLY = "RIGHT_ONLY"
    NONE_VISIBLE = "NONE_VISIBLE"
    LOW_QUALITY = "LOW_QUALITY"


class BlinkState(str, Enum):
    OPEN = "OPEN"
    CLOSING = "CLOSING"
    CLOSED = "CLOSED"
    OPENING = "OPENING"
    UNKNOWN = "UNKNOWN"

    # Backward-compatible aliases
    EYE_OPEN = "OPEN"
    EYE_CLOSING = "CLOSING"
    EYE_CLOSED = "CLOSED"
    EYE_OPENING = "OPENING"


class BlinkType(str, Enum):
    BILATERAL = "BILATERAL"
    LEFT_ONLY = "LEFT_ONLY"
    RIGHT_ONLY = "RIGHT_ONLY"
    LEFT_EYE_CLOSURE = "LEFT_EYE_CLOSURE"
    RIGHT_EYE_CLOSURE = "RIGHT_EYE_CLOSURE"
    PARTIAL = "PARTIAL"


@dataclass
class EyeBlinkConfig:
    # ── Temporal Blink Timing & Durations (ms) ──────────────────────────────────
    MIN_CLOSED_DURATION_MS: float = 50.0    # 50ms minimum closed duration
    MAX_BLINK_DURATION_MS: float = 700.0    # 700ms maximum total blink cycle
    MIN_OPEN_DURATION_MS: float = 60.0      # 60ms minimum open duration before new blink
    BLINK_DEBOUNCE_MS: float = 250.0        # 250ms refractory debounce period between blinks
    PROLONGED_CLOSURE_MS: float = 1000.0    # Sustained closure > 1.0s is looking down / resting
    REQUIRE_BILATERAL: bool = True          # Primary blink event requires bilateral closure

    # Backward-compatible duration aliases
    BLINK_MIN_DURATION_MS: float = 50.0
    BLINK_EVENT_DEBOUNCE_MS: float = 250.0

    # ── Open/Closed Classification Thresholds & Ratios ─────────────────────────
    OPEN_THRESHOLD: float = 0.22            # Absolute baseline floor for open state
    CLOSED_THRESHOLD: float = 0.16          # Absolute threshold for closed state
    BLINK_CLOSURE_RATIO: float = 0.58       # Adaptive ratio: EAR < (baseline * 0.58) -> CLOSED
    BLINK_OPEN_RATIO: float = 0.82          # Adaptive ratio: EAR >= (baseline * 0.82) -> OPEN
    DEFAULT_BASELINE_EAR: float = 0.30      # Typical human baseline open EAR
    MIN_ABSOLUTE_CLOSURE_EAR: float = 0.12  # Absolute floor
    ADAPTIVE_BASELINE_WINDOW_SEC: float = 15.0  # Rolling window to estimate baseline

    # ── Eye Quality Gate ───────────────────────────────────────────────────────
    MIN_BLUR_VAR: float = 24.0              # Minimum Laplacian variance for sharpness
    MIN_EYE_SIZE_PX: int = 10               # Minimum eye crop size in pixels
    MIN_EYE_QUALITY: float = 0.35           # Eye quality score threshold to permit blink tracking
    EYE_LOST_TIMEOUT_MS: float = 800.0      # Timeout before tracking resets after face lost
    SUNGLASSES_MAX_VAL: float = 45.0        # Max HSV value for dark lenses
    SUNGLASSES_MAX_SAT: float = 40.0        # Max HSV saturation for dark lenses

    # ── Confidence & Debounce ──────────────────────────────────────────────────
    BLINK_CONFIDENCE_THRESHOLD: float = 0.70  # Minimum confidence to confirm blink
    BLINK_MIN_CONFIDENCE: float = 0.70        # Backward-compatible alias
    TEMPORAL_SEQUENCE_LENGTH: int = 16        # Number of historical frames for 1D CNN

    # ── Interactive 25-Second Challenge ────────────────────────────────────────
    OBSERVATION_CHALLENGE_THRESHOLD_SEC: float = 25.0
    CHALLENGE_DURATION_SEC: float = 5.0
    LIVENESS_CEILING_ON_FAILED_CHALLENGE: float = 0.28

    # ── Visual Debug Mode ──────────────────────────────────────────────────────
    DEBUG_EYE_OVERLAY: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "open_threshold": self.OPEN_THRESHOLD,
            "closed_threshold": self.CLOSED_THRESHOLD,
            "min_closed_duration_ms": self.MIN_CLOSED_DURATION_MS,
            "max_blink_duration_ms": self.MAX_BLINK_DURATION_MS,
            "min_open_duration_ms": self.MIN_OPEN_DURATION_MS,
            "blink_confidence_threshold": self.BLINK_CONFIDENCE_THRESHOLD,
            "blink_debounce_ms": self.BLINK_DEBOUNCE_MS,
            "blink_min_duration_ms": self.BLINK_MIN_DURATION_MS,
            "blink_max_duration_ms": self.MAX_BLINK_DURATION_MS,
            "adaptive_closure_ratio": self.BLINK_CLOSURE_RATIO,
            "adaptive_open_ratio": self.BLINK_OPEN_RATIO,
            "min_blur_var": self.MIN_BLUR_VAR,
            "min_eye_quality": self.MIN_EYE_QUALITY,
            "challenge_threshold_sec": self.OBSERVATION_CHALLENGE_THRESHOLD_SEC,
            "require_bilateral": self.REQUIRE_BILATERAL,
        }


# Global default configuration instance
DEFAULT_CONFIG = EyeBlinkConfig()
