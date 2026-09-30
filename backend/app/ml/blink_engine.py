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


class BlinkEngine:
    """
    Session-aware temporal blink tracker.
    Accounts only for time when eyes are clearly visible and stable.
    """

    def __init__(self):
        # session_id -> session state dictionary
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def _get_or_create_session(self, session_id: str) -> Dict[str, Any]:
        now = time.time()
        if session_id not in self._sessions:
            self._sessions[session_id] = {
                "session_id": session_id,
                "created_at": now,
                "last_frame_time": now,
                "observation_seconds": 0.0,
                "is_paused": False,
                "pause_reason": None,
                "blink_count": 0,
                "last_blink_timestamp": None,
                "blink_history": [],
                "openness_history": [],  # (timestamp, openness)
                # State machine
                "state": "OPEN",  # OPEN, POSSIBLE_CLOSURE, CLOSED
                "closed_since": 0.0,
                # 25-second Challenge state
                "challenge_active": False,
                "challenge_start_time": 0.0,
                "challenge_status": None,  # None, "PENDING", "PASSED", "FAILED"
                "liveness_ceiling": 1.0,   # Default no ceiling; drops to 0.28 if challenge fails
            }
        return self._sessions[session_id]

    def reset_session(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]

    def update(
        self,
        session_id: str,
        openness: float,
        eye_analysis: Dict[str, Any],
        face_detected: bool,
    ) -> Dict[str, Any]:
        """
        Updates blink temporal state with incoming frame.
        """
        now = time.time()
        sess = self._get_or_create_session(session_id)
        dt = max(0.001, min(0.5, now - sess["last_frame_time"]))
        sess["last_frame_time"] = now

        reason_codes = []
        user_guidance = []
        just_blinked = False

        # ── 1. Observation Qualification Check ──────────────────────────────
        # Only increment observation time if eyes are clearly visible and not blurry
        eye_quality = eye_analysis.get("overall_eye_quality", 0.0)
        is_blurry = eye_analysis.get("is_blurry", False)
        is_obscured = eye_analysis.get("is_obscured", False)
        eyes_visible = eye_analysis.get("left_eye_visible", False) or eye_analysis.get("right_eye_visible", False)

        can_observe_eyes = (
            face_detected
            and eyes_visible
            and not is_blurry
            and not is_obscured
            and eye_quality >= 0.35
        )

        if can_observe_eyes:
            sess["is_paused"] = False
            sess["pause_reason"] = None
            sess["observation_seconds"] += dt
        else:
            sess["is_paused"] = True
            if not face_detected:
                sess["pause_reason"] = "FACE_NOT_IN_FRAME"
            elif is_obscured:
                sess["pause_reason"] = "EYES_OBSCURED"
            elif is_blurry:
                sess["pause_reason"] = "EYES_TOO_BLURRY"
            else:
                sess["pause_reason"] = "EYES_NOT_VISIBLE"

        # ── 2. Adaptive Openness Thresholds ─────────────────────────────────
        sess["openness_history"].append((now, openness))
        # Keep 15 seconds history
        sess["openness_history"] = [pt for pt in sess["openness_history"] if now - pt[0] <= 15.0]

        if len(sess["openness_history"]) >= 6:
            vals = [v for _, v in sess["openness_history"]]
            baseline = float(np.percentile(vals, 75))
        else:
            baseline = openness if openness > 0 else 18.0

        if baseline <= 1.0:
            threshold_close = max(0.08, baseline * 0.58)
            threshold_open = max(0.12, baseline * 0.80)
        else:
            threshold_close = max(4.0, baseline * 0.60)
            threshold_open = max(6.0, baseline * 0.82)

        # ── 3. Biological Blink State Machine ───────────────────────────────
        if can_observe_eyes:
            if sess["state"] == "OPEN":
                if openness < threshold_close:
                    sess["state"] = "CLOSED"
                    sess["closed_since"] = now
            elif sess["state"] == "CLOSED":
                if openness >= threshold_open:
                    duration = now - sess["closed_since"]
                    # Biological human blink verification: 80ms <= duration <= 700ms
                    if MIN_BLINK_DURATION <= duration <= MAX_BLINK_DURATION:
                        # Refractory period check: >= 300ms from last blink
                        if (
                            sess["last_blink_timestamp"] is None
                            or (now - sess["last_blink_timestamp"]) >= BLINK_REFRACTORY_PERIOD
                        ):
                            sess["blink_count"] += 1
                            sess["last_blink_timestamp"] = now
                            sess["blink_history"].append(now)
                            just_blinked = True
                            reason_codes.append("BLINK_DETECTED")
                            # If challenge was active, pass it!
                            if sess["challenge_active"]:
                                sess["challenge_active"] = False
                                sess["challenge_status"] = "PASSED"
                                sess["observation_seconds"] = 0.0  # Reset 25s timer on passed challenge
                                sess["liveness_ceiling"] = 1.0     # Lift ceiling
                                reason_codes.append("BLINK_CHALLENGE_PASSED")
                    sess["state"] = "OPEN"
                elif (now - sess["closed_since"]) > 1.2:
                    # Eye closed for > 1.2s -> Prolonged closure / looking down (not a blink)
                    sess["state"] = "OPEN"
        else:
            # If tracking was lost, reset state machine to prevent counting reconnection as blink
            sess["state"] = "OPEN"

        # ── 4. 25-Second No-Blink Challenge Protocol ────────────────────────
        seconds_since_last_blink = (
            (now - sess["last_blink_timestamp"])
            if sess["last_blink_timestamp"] is not None
            else sess["observation_seconds"]
        )

        challenge_countdown = None

        if (
            sess["observation_seconds"] >= OBSERVATION_CHALLENGE_THRESHOLD
            and (sess["last_blink_timestamp"] is None or (now - sess["last_blink_timestamp"]) >= OBSERVATION_CHALLENGE_THRESHOLD)
        ):
            if not sess["challenge_active"] and sess["challenge_status"] != "FAILED":
                # Trigger the interactive challenge
                sess["challenge_active"] = True
                sess["challenge_start_time"] = now
                sess["challenge_status"] = "ACTIVE"
                reason_codes.append("BLINK_CHALLENGE_REQUESTED")

        if sess["challenge_active"]:
            elapsed = now - sess["challenge_start_time"]
            remaining = max(0.0, CHALLENGE_DURATION - elapsed)
            challenge_countdown = int(np.ceil(remaining))

            if remaining <= 0.0:
                # Challenge expired without a valid blink
                sess["challenge_active"] = False
                sess["challenge_status"] = "FAILED"
                sess["liveness_ceiling"] = 0.28  # Strict 20-30% ceiling on liveness
                reason_codes.append("BLINK_CHALLENGE_FAILED")
                user_guidance.append(
                    "No clear blink was detected during the verification window. Liveness confidence reduced."
                )

        # Rate evaluation in rolling 10 seconds
        recent_blinks = [t for t in sess["blink_history"] if now - t <= 10.0]
        blinks_10s = len(recent_blinks)

        return {
            "blink_count": int(sess["blink_count"]),
            "last_blink_timestamp": sess["last_blink_timestamp"],
            "seconds_since_last_blink": round(float(seconds_since_last_blink), 1),
            "continuous_observation_sec": round(float(sess["observation_seconds"]), 1),
            "is_timer_paused": bool(sess["is_paused"]),
            "timer_pause_reason": sess["pause_reason"],
            "just_blinked": bool(just_blinked),
            "blinks_in_last_10s": int(blinks_10s),
            "challenge": {
                "active": bool(sess["challenge_active"]),
                "status": sess["challenge_status"],
                "countdown": challenge_countdown,
                "label": "PLEASE BLINK" if sess["challenge_active"] else None,
                "prompt": (
                    "We haven't detected a clear blink in 25 seconds of clear observation. "
                    "Please blink once to continue verification."
                    if sess["challenge_active"]
                    else None
                ),
            },
            "liveness_ceiling": float(sess["liveness_ceiling"]),
            "reason_codes": reason_codes,
            "user_guidance": user_guidance,
        }


# Global singleton instance
blink_engine = BlinkEngine()
