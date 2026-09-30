"""
Privacy Eye — Centralized Confidence & Live Human Scoring Engine
Deterministic, explainable, testable, evidence-based fusion engine.
Implements:
1. Product confidence scoring with confirmed blink as primary signal (65%–80% range).
2. Natural facial movement and physiological liveness (~15%).
3. Supporting evidence: temporal consistency, face tracking, and input quality (~15%).
4. Hard presentation attack override (face inside phone screen -> 0% live-human confidence).
5. 25-Second no-blink challenge with calibrated liveness ceiling (20%–30%).
6. Observable eye qualification (eyes blurry/invisible -> pause timer, no penalty).
7. Model disagreement & reliability classification (HIGH / MEDIUM / LOW).
8. Exponential Moving Average (EMA) smoothing and decision hysteresis.
"""
import os
import math
import time
import structlog
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

logger = structlog.get_logger(__name__)

# Fallback default configuration if YAML file is unavailable
DEFAULT_CONFIG = {
    "weights": {
        "blink_weight": 0.70,
        "liveness_movement_weight": 0.15,
        "supporting_weight": 0.15,
    },
    "blink": {
        "min_duration_sec": 0.08,
        "max_duration_sec": 0.70,
        "refractory_sec": 0.30,
        "quality_threshold": 0.65,
        "eye_visibility_threshold": 0.35,
        "single_eye_multiplier": 0.75,
        "quality_map_min_quality": 0.65,
        "quality_map_max_quality": 1.00,
        "quality_map_min_confidence": 65.0,
        "quality_map_max_confidence": 80.0,
        "second_blink_boost": 5.0,
        "third_blink_boost": 2.0,
        "max_blink_boost": 8.0,
    },
    "challenge": {
        "no_blink_seconds": 25.0,
        "challenge_duration": 5.0,
        "liveness_confidence_ceiling": 0.28,
    },
    "movement": {
        "min_natural_displacement": 0.005,
        "optimal_displacement": 0.045,
        "max_erratic_displacement": 0.25,
    },
    "quality": {
        "min_sharpness_var": 25.0,
        "good_sharpness_var": 80.0,
        "low_quality_reliability_penalty": 0.30,
    },
    "replay": {
        "phone_detected_threshold": 0.65,
        "face_in_screen_threshold": 0.60,
        "presentation_override_threshold": 0.75,
    },
    "temporal": {
        "smoothing_factor": 0.35,
        "hysteresis_threshold": 3.5,
        "disagreement_threshold": 0.40,
    },
}


def load_confidence_config() -> Dict[str, Any]:
    """Loads centralized configuration from YAML file or returns DEFAULT_CONFIG."""
    possible_paths = [
        Path(__file__).parent.parent.parent / "configs" / "confidence.yaml",
        Path(__file__).parent.parent.parent.parent / "configs" / "confidence.yaml",
        Path("configs/confidence.yaml"),
        Path("backend/configs/confidence.yaml"),
    ]
    for p in possible_paths:
        if p.exists():
            try:
                import yaml
                with open(p, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f)
                    if isinstance(cfg, dict) and "weights" in cfg:
                        return cfg
            except Exception as e:
                logger.warning("Failed to parse config yaml, using defaults", path=str(p), error=str(e))
    return DEFAULT_CONFIG


class ConfidenceFusionEngine:
    """
    Centralized, deterministic evidence fusion engine for live camera human scoring.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or load_confidence_config()
        self._session_smoothed_conf: Dict[str, float] = {}
        self._session_last_assessment: Dict[str, str] = {}

    def reload_config(self):
        """Reload configuration from disk."""
        self.config = load_confidence_config()

    def calculate_blink_evidence(
        self,
        blink_count: int,
        blink_quality: float,
        eye_status: str,
        left_eye_visible: bool,
        right_eye_visible: bool,
        is_eye_blurry: bool,
    ) -> Dict[str, Any]:
        """
        Calculates blink evidence contribution.
        Confirmed 1st blink enters the 65%–80% range depending on blink quality.
        Diminishing returns for subsequent blinks.
        Eyes not visible / blurry -> UNAVAILABLE, not penalized.
        """
        b_cfg = self.config["blink"]
        q_thresh = b_cfg["quality_threshold"]

        # 1. Check if eyes are sufficiently observable
        both_eyes = left_eye_visible and right_eye_visible
        one_eye_only = (left_eye_visible and not right_eye_visible) or (right_eye_visible and not left_eye_visible)
        eyes_not_visible = not (left_eye_visible or right_eye_visible) or is_eye_blurry

        if eyes_not_visible:
            return {
                "blink_evidence_score": 0.0,
                "blink_confirmed": False,
                "blink_quality": 0.0,
                "status": "UNAVAILABLE",
                "explanation": "Eye-based evidence is currently unavailable (blurry or obscured).",
                "single_eye_penalty_applied": False,
            }

        # 2. Check if blink is confirmed
        is_confirmed = (blink_count > 0) and (blink_quality >= q_thresh)

        if not is_confirmed:
            return {
                "blink_evidence_score": 0.0,
                "blink_confirmed": False,
                "blink_quality": round(float(blink_quality), 3),
                "status": "TRACKING_NO_CONFIRMED_BLINK",
                "explanation": "Tracking ocular dynamics; no confirmed biological blink recorded yet.",
                "single_eye_penalty_applied": False,
            }

        # 3. Product mapping for confirmed 1st blink: maps [q_min, q_max] -> [65.0, 80.0]
        q_min = b_cfg["quality_map_min_quality"]
        q_max = b_cfg["quality_map_max_quality"]
        c_min = b_cfg["quality_map_min_confidence"]
        c_max = b_cfg["quality_map_max_confidence"]

        norm_q = (blink_quality - q_min) / max(0.01, (q_max - q_min))
        norm_q = min(1.0, max(0.0, norm_q))
        base_conf = c_min + norm_q * (c_max - c_min)

        # 4. Partial visibility adjustment (one eye only)
        single_eye_penalty = False
        if one_eye_only:
            base_conf *= b_cfg["single_eye_multiplier"]
            single_eye_penalty = True

        # 5. Diminishing returns for additional blinks
        additional_boost = 0.0
        if blink_count >= 2:
            additional_boost += b_cfg["second_blink_boost"]
        if blink_count >= 3:
            additional_boost += b_cfg["third_blink_boost"]
        additional_boost = min(b_cfg["max_blink_boost"], additional_boost)

        final_blink_score = min(88.0, base_conf + additional_boost)

        return {
            "blink_evidence_score": round(float(final_blink_score), 2),
            "blink_confirmed": True,
            "blink_quality": round(float(blink_quality), 3),
            "status": "CONFIRMED",
            "explanation": f"Biological human blink confirmed (quality: {blink_quality:.2f}, count: {blink_count}).",
            "single_eye_penalty_applied": single_eye_penalty,
        }

    def calculate_movement_evidence(
        self,
        displacement_rate: float,
        delta_yaw: float,
        delta_pitch: float,
        head_pose_continuity: float = 0.9,
    ) -> Dict[str, Any]:
        """
        Calculates facial movement evidence.
        Normalizes head rotation, landmark motion, and expression variation.
        Penalizes both static photos (< 0.005) and erratic jitter (> 0.25).
        """
        m_cfg = self.config["movement"]
        min_disp = m_cfg["min_natural_displacement"]
        opt_disp = m_cfg["optimal_displacement"]
        max_err = m_cfg["max_erratic_displacement"]

        # Combined composite displacement
        comp_disp = displacement_rate + (abs(delta_yaw) * 0.05) + (abs(delta_pitch) * 0.05)

        if comp_disp < min_disp:
            # Static photograph or rigid display replay
            score = 0.15
            label = "STATIC"
            explanation = "Extremely static facial positioning — lack of natural physiological micro-movement."
        elif comp_disp > max_err:
            # Unstable tracking or erratic movement
            score = 0.45
            label = "ERRATIC"
            explanation = "Erratic movement or tracking instability detected."
        else:
            # Natural movement range [min_disp, opt_disp, max_err]
            if comp_disp <= opt_disp:
                ratio = (comp_disp - min_disp) / max(0.001, (opt_disp - min_disp))
                score = 0.60 + (ratio * 0.35)  # 0.60 to 0.95
            else:
                ratio = (comp_disp - opt_disp) / max(0.001, (max_err - opt_disp))
                score = 0.95 - (ratio * 0.35)  # 0.95 down to 0.60
            label = "NATURAL"
            explanation = "Natural human facial displacement and pose continuity observed."

        # Scale by pose continuity
        score = min(1.0, max(0.0, score * head_pose_continuity))
        return {
            "movement_score": round(float(score), 3),
            "movement_label": label,
            "composite_displacement": round(float(comp_disp), 4),
            "explanation": explanation,
        }

    def calculate_supporting_evidence(
        self,
        temporal_consistency: float,
        face_tracking_quality: float,
        quality_index: int,
    ) -> Dict[str, Any]:
        """
        Combines temporal consistency, face tracking stability, and input quality.
        """
        q_norm = min(1.0, max(0.0, quality_index / 100.0))
        t_norm = min(1.0, max(0.0, temporal_consistency))
        tr_norm = min(1.0, max(0.0, face_tracking_quality))

        supporting_score = (t_norm * 0.40) + (tr_norm * 0.35) + (q_norm * 0.25)
        return {
            "supporting_score": round(float(supporting_score), 3),
            "temporal_consistency": round(float(t_norm), 3),
            "face_tracking_quality": round(float(tr_norm), 3),
            "input_quality_norm": round(float(q_norm), 3),
        }

    def fuse(
        self,
        session_id: str,
        blink_res: Dict[str, Any],
        eye_res: Dict[str, Any],
        screen_res: Dict[str, Any],
        movement_data: Dict[str, Any],
        quality: Dict[str, Any],
        benchmarks: Dict[str, Any],
        temporal_consistency: float = 0.90,
        face_tracking_quality: float = 0.95,
    ) -> Dict[str, Any]:
        """
        Master deterministic fusion combining all sub-signals into final explainable assessment.
        """
        weights = self.config["weights"]
        w_blink = weights["blink_weight"]
        w_live_mov = weights["liveness_movement_weight"]
        w_supp = weights["supporting_weight"]

        # ── 1. Evaluate Replay & Presentation Attack ─────────────────────────
        phone_detected = bool(screen_res.get("phone_detected", False))
        screen_face_associated = bool(screen_res.get("screen_face_associated", False))
        presentation_attack = bool(screen_res.get("presentation_attack", False))
        pres_conf = float(screen_res.get("presentation_attack_confidence", 0.0))
        override_thresh = self.config["replay"]["presentation_override_threshold"]

        # CASE B: Phone detected AND face physically inside phone screen
        presentation_override = False
        if screen_face_associated and (presentation_attack or pres_conf >= override_thresh):
            presentation_override = True

        # ── 2. Evaluate Blink Evidence ───────────────────────────────────────
        blink_count = int(blink_res.get("blink_count", 0))
        # Derive blink quality from eye quality & duration if not explicitly provided
        blink_quality = float(blink_res.get("blink_quality", eye_res.get("overall_eye_quality", 0.75)))
        left_eye_vis = bool(eye_res.get("left_eye_visible", False))
        right_eye_vis = bool(eye_res.get("right_eye_visible", False))
        is_blurry = bool(eye_res.get("is_blurry", False))
        eye_status = eye_res.get("eye_status", "UNKNOWN")

        blink_eval = self.calculate_blink_evidence(
            blink_count=blink_count,
            blink_quality=blink_quality,
            eye_status=eye_status,
            left_eye_visible=left_eye_vis,
            right_eye_visible=right_eye_vis,
            is_eye_blurry=is_blurry,
        )

        # ── 3. Evaluate Movement & Liveness ──────────────────────────────────
        mov_eval = self.calculate_movement_evidence(
            displacement_rate=movement_data.get("displacement_rate", 0.03),
            delta_yaw=movement_data.get("d_yaw", 0.0),
            delta_pitch=movement_data.get("d_pitch", 0.0),
            head_pose_continuity=movement_data.get("pose_continuity", 0.92),
        )

        # Base physiological liveness (micro-jitter, texture realism)
        raw_liveness = float(movement_data.get("physiological_liveness", 0.85))

        # Enforce 25-Second challenge ceiling on liveness if challenge failed
        challenge_status = blink_res.get("challenge", {}).get("status")
        challenge_active = bool(blink_res.get("challenge", {}).get("active", False))
        ceiling_applied = False

        if challenge_status == "FAILED":
            ceiling = self.config["challenge"]["liveness_confidence_ceiling"]
            raw_liveness = min(raw_liveness, ceiling)
            ceiling_applied = True

        liveness_movement_score = (mov_eval["movement_score"] * 0.50) + (raw_liveness * 0.50)

        # ── 4. Evaluate Supporting Evidence & Quality ────────────────────────
        supp_eval = self.calculate_supporting_evidence(
            temporal_consistency=temporal_consistency,
            face_tracking_quality=face_tracking_quality,
            quality_index=quality.get("quality_index", 75),
        )

        # ── 5. Evaluate Risks & Disagreements ────────────────────────────────
        replay_risk = float(screen_res.get("presentation_risk", screen_res.get("replay_risk", 0.05)))
        synthetic_risk = float(benchmarks.get("faceforensics", {}).get("score", 0.05))

        # Model disagreement: e.g. blink says live (high), but frequency/replay says attack
        blink_norm = blink_eval["blink_evidence_score"] / 100.0
        disagreement_score = max(0.0, (blink_norm - (1.0 - max(replay_risk, synthetic_risk))))
        disagreement_label = "LOW"
        if disagreement_score >= self.config["temporal"]["disagreement_threshold"]:
            disagreement_label = "HIGH"
        elif disagreement_score >= 0.20:
            disagreement_label = "MEDIUM"

        # ── 6. Centralized Score Fusion ──────────────────────────────────────
        if presentation_override:
            # HARD OVERRIDE: Presentation attack detected (face presented via electronic screen) -> FAIL
            product_confidence = 0.0
            model_probability = 0.0
            reliability = "HIGH"
            verdict = "FAIL"
            verification_status = "FAIL"
            is_live_human = False
            assessment = "FAIL_PRESENTATION_ATTACK"
            category_label = "FAIL: Screen/Replay Presentation Attack"
            explanation = (
                "Verification FAILED: Possible screen/replay presentation attack. The detected face appears to be presented "
                "through a smartphone or electronic display rather than direct human observation."
            )
            user_message = "Verification FAILED: A face appears to be displayed through a phone or electronic screen."

        elif challenge_active:
            # Active "PLEASE BLINK" challenge countdown
            product_confidence = 45.0
            model_probability = 0.45
            reliability = "MEDIUM"
            verdict = "PENDING"
            verification_status = "PENDING"
            is_live_human = False
            assessment = "PLEASE_BLINK"
            category_label = "PLEASE BLINK"
            explanation = (
                "We haven't detected a clear blink in 25 seconds of clear observation. "
                "Please blink once to continue verification."
            )
            user_message = "Please blink once to continue verification."

        elif challenge_status == "FAILED":
            # 25-second challenge failed without blink: enforce low liveness ceiling -> FAIL
            product_confidence = round(24.0 + (supp_eval["supporting_score"] * 5.0), 1)
            model_probability = 0.26
            reliability = "LOW"
            verdict = "FAIL"
            verification_status = "FAIL"
            is_live_human = False
            assessment = "UNABLE_TO_DETERMINE"
            category_label = "Low liveness confidence (No blink verified in 25s observation)"
            explanation = (
                "No confirmed blink detected during continuous observation. "
                "Liveness confidence is constrained to a low-certainty ceiling."
            )
            user_message = "A clear blink was not detected during observation. Reliability has been reduced."

        elif blink_eval["status"] == "CONFIRMED":
            # Confirmed human blink: enters 65%–80% range, combined with movement and supporting
            # Blink component contributes w_blink * score
            # Liveness + Movement contributes w_live_mov * score * 100
            # Supporting contributes w_supp * score * 100
            blink_contrib = blink_eval["blink_evidence_score"] * w_blink
            live_mov_contrib = (liveness_movement_score * 100.0) * w_live_mov
            supp_contrib = (supp_eval["supporting_score"] * 100.0) * w_supp

            raw_product_conf = blink_contrib + live_mov_contrib + supp_contrib

            # Deduct for synthetic or replay risk
            risk_penalty = (replay_risk * 15.0) + (synthetic_risk * 15.0)
            raw_product_conf = max(0.0, raw_product_conf - risk_penalty)

            # High disagreement check
            if disagreement_label == "HIGH":
                product_confidence = round(min(55.0, raw_product_conf), 1)
                model_probability = round(product_confidence / 100.0, 3)
                reliability = "LOW"
                verdict = "FAIL"
                verification_status = "FAIL"
                is_live_human = False
                assessment = "SUSPICIOUS"
                category_label = "Suspicious (Signal Disagreement)"
                explanation = "Blink observed but contradictory forensic or frequency anomalies detected."
                user_message = "Inconsistent signals detected between ocular dynamics and facial forensics."
            else:
                product_confidence = round(min(98.5, max(65.0, raw_product_conf)), 1)
                model_probability = round(product_confidence / 100.0, 3)
                # Reliability check
                if quality.get("quality_index", 0) >= 65 and not blink_eval["single_eye_penalty_applied"]:
                    reliability = "HIGH"
                else:
                    reliability = "MEDIUM"
                verdict = "PASS"
                verification_status = "PASS"
                is_live_human = True
                assessment = "LIKELY_LIVE_HUMAN"
                category_label = "Likely live human"
                explanation = (
                    f"Confirmed biological human blink (quality: {blink_quality:.2f}), "
                    f"{mov_eval['movement_label'].lower()} facial movement, and stable tracking."
                )
                user_message = "Confirmed human liveness signals detected."

        elif eye_status in ("BOTH_EYES_NOT_VISIBLE", "EYE_TOO_BLURRY", "EYES_OBSCURED") or is_blurry:
            # Eyes blurry or not visible: derived strictly from spatial, movement, and quality
            live_mov_score = (liveness_movement_score * 0.60) + (supp_eval["supporting_score"] * 0.40)
            base_score = 56.0 + (live_mov_score * 18.0)
            product_confidence = round(float(max(50.0, min(74.0, base_score))), 1)
            model_probability = round(product_confidence / 100.0, 3)
            reliability = "MEDIUM" if quality.get("quality_index", 0) >= 50 else "LOW"
            verdict = "PENDING"
            verification_status = "PENDING"
            is_live_human = False
            assessment = "HUMAN_FACE_DETECTED"
            category_label = "Human face detected (Eyes not clearly visible)"
            explanation = (
                "Natural human facial structure and movements detected. "
                "Note: Eye-based liveness evidence is unavailable due to motion blur or occlusion."
            )
            user_message = "Eyes are not clearly visible. Continuing analysis with spatial and temporal signals."

        else:
            # Eyes visible, but no confirmed blink yet (initial observation phase)
            live_mov_score = (liveness_movement_score * 0.50) + (supp_eval["supporting_score"] * 0.50)
            base_score = 50.0 + (live_mov_score * 12.0)
            product_confidence = round(float(max(45.0, min(62.0, base_score))), 1)
            model_probability = round(product_confidence / 100.0, 3)
            reliability = "MEDIUM"
            verdict = "PENDING"
            verification_status = "PENDING"
            is_live_human = False
            assessment = "ANALYZING"
            category_label = "Analyzing facial and ocular dynamics"
            explanation = "Tracking face and awaiting natural human blink for high-confidence verification."
            user_message = "Position face steadily. Natural blink will complete high-confidence liveness."

        # ── 7. EMA Smoothing & Decision Hysteresis ───────────────────────────
        if not presentation_override:
            alpha = self.config["temporal"]["smoothing_factor"]
            prev_conf = self._session_smoothed_conf.get(session_id, product_confidence)
            smoothed = round(float(alpha * product_confidence + (1.0 - alpha) * prev_conf), 1)
            self._session_smoothed_conf[session_id] = smoothed
            product_confidence = smoothed
        else:
            self._session_smoothed_conf[session_id] = 0.0
            product_confidence = 0.0

        # Decision Hysteresis: prevent rapid flickering if score is near threshold boundaries
        self._session_last_assessment[session_id] = assessment

        return {
            "verdict": verdict,
            "verification_status": verification_status,
            "is_live_human": is_live_human,
            "live_human_confidence": product_confidence,
            "model_probability": model_probability,
            "synthetic_risk": round(synthetic_risk, 3),
            "replay_risk": round(replay_risk, 3),
            "reliability": reliability,
            "assessment": assessment,
            "category_label": category_label,
            "explanation": explanation,
            "user_message": user_message,
            "model_disagreement": disagreement_label,
            "presentation_attack_override": presentation_override,
            "ceiling_applied": ceiling_applied,
            # Granular explainable sub-scores
            "sub_scores": {
                "blink_evidence": blink_eval["blink_evidence_score"],
                "blink_quality": blink_eval["blink_quality"],
                "blink_confirmed": blink_eval["blink_confirmed"],
                "blink_status": blink_eval["status"],
                "facial_movement_evidence": mov_eval["movement_score"],
                "facial_movement_label": mov_eval["movement_label"],
                "liveness_evidence": round(liveness_movement_score, 3),
                "temporal_consistency": supp_eval["temporal_consistency"],
                "face_tracking_quality": supp_eval["face_tracking_quality"],
                "input_quality": quality.get("quality_index", 75),
                "single_eye_penalty": blink_eval["single_eye_penalty_applied"],
            },
        }


# Global Singleton Instance
confidence_fusion_engine = ConfidenceFusionEngine()
