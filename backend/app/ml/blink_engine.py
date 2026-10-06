"""
Privacy Eye — Advanced Blink State Machine, Timer, & 25-Second Challenge Engine
Enforces biological blink validation (80ms - 700ms), continuous observation qualification,
and uncertainty-aware liveness ceiling constraints.
"""
import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

MIN_BLINK_DURATION = 0.08   # 80ms minimum for biological human blink
MAX_BLINK_DURATION = 0.70   # 700ms maximum duration
BLINK_REFRACTORY_PERIOD = 0.30  # 300ms refractory period between blinks
OBSERVATION_CHALLENGE_THRESHOLD = 25.0  # 25 seconds of clear observation
CHALLENGE_DURATION = 5.0    # 5 seconds to comply with "PLEASE BLINK"


import time
import numpy as np
from typing import Dict, Any, List, Optional, Tuple

from app.ml.configs.eye_blink_config import (
    EyeVisibilityState,
    BlinkState,
    BlinkType,
    EyeBlinkConfig,
    DEFAULT_CONFIG,
)
from app.ml.blink_detection.blink_state_machine import TemporalBlinkStateMachine


class BlinkEngine:
    """
    Session-aware temporal blink tracker.
    Enforces biological blink validation (OPEN -> CLOSING -> CLOSED -> OPENING -> OPEN),
    continuous observation qualification, anti-duplicate debouncing, and 25s challenge constraints.
    """

    def __init__(self, config: Optional[EyeBlinkConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self._sm = TemporalBlinkStateMachine(config=self.config)

    def _get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        sess = self._sm._get_or_create_session(session_id)
        sess["blink_count"] = sess["total_blinks"]
        return sess

    def reset_session(self, session_id: str):
        self._sm.reset_session(session_id)

    def update(
        self,
        session_id: str,
        openness: float,
        eye_analysis: Dict[str, Any],
        face_detected: bool,
        head_pose: Optional[Dict[str, float]] = None,
        timestamp_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Updates temporal blink state with incoming frame.
        Guarantees: EYES OPEN -> EYES CLOSED -> EYES OPEN = ONE VALID BLINK.
        """
        eye_d = dict(eye_analysis)
        if "mean_ear" not in eye_d:
            eye_d["mean_ear"] = openness
        if "left_ear" not in eye_d:
            eye_d["left_ear"] = openness
        if "right_ear" not in eye_d:
            eye_d["right_ear"] = openness

        return self._sm.update(
            session_id=session_id,
            eye_data=eye_d,
            face_detected=face_detected,
            head_pose=head_pose,
            timestamp_ms=timestamp_ms,
        )


# Global singleton instance
blink_engine = BlinkEngine()

