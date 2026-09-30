"""
Privacy Eye — Comprehensive Unit & Integration Tests:
Confidence Fusion Engine, Blink-Based Liveness Scoring, Presentation Attack Overrides,
25-Second Observation Challenges, and Temporal Disagreement Mechanics.
"""
import time
import pytest
import numpy as np
import cv2

from app.ml.confidence_fusion import ConfidenceFusionEngine, load_confidence_config
from app.ml.blink_engine import BlinkEngine
from app.ml.eye_analyzer import (
    EyeAnalyzer,
    BOTH_EYES_VISIBLE,
    LEFT_ONLY,
    RIGHT_ONLY,
    BOTH_EYES_NOT_VISIBLE,
    EYE_TOO_BLURRY,
    EYES_OBSCURED,
)
from app.ml.screen_detector import ScreenDetector
from app.ml.live_authenticity import live_authenticity_engine


# ── TEST SUITE: CONFIDENCE FUSION ENGINE & EXACT RULES ─────────────────────────

def test_load_config():
    """Verify that centralized confidence configuration loads correctly with all required keys."""
    cfg = load_confidence_config()
    assert "weights" in cfg
    assert "blink" in cfg
    assert "challenge" in cfg
    assert "movement" in cfg
    assert "replay" in cfg
    assert cfg["weights"]["blink_weight"] == 0.70
    assert cfg["weights"]["liveness_movement_weight"] == 0.15
    assert cfg["weights"]["supporting_weight"] == 0.15


# ── TEST A: ONE HIGH-QUALITY BLINK + STRONG MOVEMENT + STRONG LIVENESS ─────────
def test_rule_test_a_one_high_quality_blink_enters_65_to_80_range():
    """
    TEST A:
    One high-quality blink (quality 0.85) + strong natural facial movement (0.85)
    + strong physiological liveness (0.90) + stable tracking.
    Expectation: Live human confidence enters the configured high range (75%–88%).
    """
    engine = ConfidenceFusionEngine()
    session_id = "test_a_session"

    blink_res = {
        "blink_count": 1,
        "blink_quality": 0.88,
        "is_timer_paused": False,
        "challenge": {"active": False, "status": None},
    }
    eye_res = {
        "left_eye_visible": True,
        "right_eye_visible": True,
        "is_blurry": False,
        "eye_status": BOTH_EYES_VISIBLE,
        "overall_eye_quality": 0.88,
    }
    screen_res = {
        "phone_detected": False,
        "screen_face_associated": False,
        "presentation_attack": False,
        "presentation_attack_confidence": 0.05,
        "presentation_risk": 0.04,
    }
    movement_data = {
        "displacement_rate": 0.045,  # Optimal natural range
        "d_yaw": 0.02,
        "d_pitch": 0.015,
        "pose_continuity": 0.95,
        "physiological_liveness": 0.90,
    }
    quality = {"quality_index": 82}
    benchmarks = {"faceforensics": {"score": 0.04}}

    res = engine.fuse(
        session_id=session_id,
        blink_res=blink_res,
        eye_res=eye_res,
        screen_res=screen_res,
        movement_data=movement_data,
        quality=quality,
        benchmarks=benchmarks,
        temporal_consistency=0.92,
        face_tracking_quality=0.95,
    )

    assert res["assessment"] == "LIKELY_LIVE_HUMAN"
    assert res["reliability"] == "HIGH"
    assert 65.0 <= res["live_human_confidence"] <= 88.0
    assert res["sub_scores"]["blink_confirmed"] is True
    assert res["presentation_attack_override"] is False


# ── TEST B: ONE WEAK BLINK + WEAK MOVEMENT + WEAK LIVENESS ─────────────────────
def test_rule_test_b_one_weak_blink_lower_confidence():
    """
    TEST B:
    Weak blink quality (0.66) + weak/static facial movement + lower liveness.
    Expectation: Lower confidence and reduced reliability.
    """
    engine = ConfidenceFusionEngine()
    session_id = "test_b_session"

    blink_res = {
        "blink_count": 1,
        "blink_quality": 0.66,
        "is_timer_paused": False,
        "challenge": {"active": False, "status": None},
    }
    eye_res = {
        "left_eye_visible": True,
        "right_eye_visible": True,
        "is_blurry": False,
        "eye_status": BOTH_EYES_VISIBLE,
        "overall_eye_quality": 0.55,
    }
    screen_res = {
        "phone_detected": False,
        "screen_face_associated": False,
        "presentation_attack": False,
        "presentation_attack_confidence": 0.15,
        "presentation_risk": 0.12,
    }
    movement_data = {
        "displacement_rate": 0.003,  # Too static
        "d_yaw": 0.001,
        "d_pitch": 0.001,
        "pose_continuity": 0.70,
        "physiological_liveness": 0.50,
    }
    quality = {"quality_index": 52}
    benchmarks = {"faceforensics": {"score": 0.15}}

    res = engine.fuse(
        session_id=session_id,
        blink_res=blink_res,
        eye_res=eye_res,
        screen_res=screen_res,
        movement_data=movement_data,
        quality=quality,
        benchmarks=benchmarks,
        temporal_consistency=0.75,
        face_tracking_quality=0.80,
    )

    # Confidence must be lower than in Test A, reliability is reduced
    assert res["reliability"] in ("MEDIUM", "LOW")
    assert res["live_human_confidence"] < 75.0


# ── TEST C: 25-SECOND NO-BLINK CHALLENGE FAILURE CONSTRAINED TO 20-30% ─────────
def test_rule_test_c_25_second_challenge_failure_constrained_ceiling():
    """
    TEST C:
    Eyes continuously visible for 25s, no blink occurred, and challenge failed.
    Expectation: Live human confidence constrained to ~20%–30% ceiling, assessment UNABLE_TO_DETERMINE.
    """
    engine = ConfidenceFusionEngine()
    session_id = "test_c_session"

    blink_res = {
        "blink_count": 0,
        "blink_quality": 0.0,
        "is_timer_paused": False,
        "challenge": {"active": False, "status": "FAILED"},
    }
    eye_res = {
        "left_eye_visible": True,
        "right_eye_visible": True,
        "is_blurry": False,
        "eye_status": BOTH_EYES_VISIBLE,
        "overall_eye_quality": 0.85,
    }
    screen_res = {
        "phone_detected": False,
        "screen_face_associated": False,
        "presentation_attack": False,
        "presentation_attack_confidence": 0.02,
        "presentation_risk": 0.02,
    }
    movement_data = {
        "displacement_rate": 0.035,
        "d_yaw": 0.01,
        "d_pitch": 0.01,
        "pose_continuity": 0.90,
        "physiological_liveness": 0.85,
    }
    quality = {"quality_index": 80}
    benchmarks = {"faceforensics": {"score": 0.02}}

    res = engine.fuse(
        session_id=session_id,
        blink_res=blink_res,
        eye_res=eye_res,
        screen_res=screen_res,
        movement_data=movement_data,
        quality=quality,
        benchmarks=benchmarks,
    )

    assert res["assessment"] == "UNABLE_TO_DETERMINE"
    assert res["ceiling_applied"] is True
    assert res["reliability"] == "LOW"
    assert 20.0 <= res["live_human_confidence"] <= 32.0


# ── TEST D: EYES NOT VISIBLE -> TIMER PAUSED -> NO PENALTY ─────────────────────
def test_rule_test_d_eyes_not_visible_pauses_timer_no_penalty():
    """
    TEST D:
    Eyes blurry or not visible -> blink evidence is UNAVAILABLE,
    no 25-second penalty is applied, assessment is HUMAN_FACE_DETECTED.
    """
    engine = ConfidenceFusionEngine()
    session_id = "test_d_session"

    blink_res = {
        "blink_count": 0,
        "blink_quality": 0.0,
        "is_timer_paused": True,
        "timer_pause_reason": "EYES_TOO_BLURRY",
        "challenge": {"active": False, "status": None},
    }
    eye_res = {
        "left_eye_visible": False,
        "right_eye_visible": False,
        "is_blurry": True,
        "eye_status": EYE_TOO_BLURRY,
        "overall_eye_quality": 0.15,
    }
    screen_res = {
        "phone_detected": False,
        "screen_face_associated": False,
        "presentation_attack": False,
        "presentation_attack_confidence": 0.05,
    }
    movement_data = {
        "displacement_rate": 0.04,
        "d_yaw": 0.02,
        "d_pitch": 0.01,
        "pose_continuity": 0.90,
        "physiological_liveness": 0.80,
    }
    quality = {"quality_index": 55}
    benchmarks = {"faceforensics": {"score": 0.05}}

    res = engine.fuse(
        session_id=session_id,
        blink_res=blink_res,
        eye_res=eye_res,
        screen_res=screen_res,
        movement_data=movement_data,
        quality=quality,
        benchmarks=benchmarks,
    )

    assert res["assessment"] == "HUMAN_FACE_DETECTED"
    assert res["sub_scores"]["blink_status"] == "UNAVAILABLE"
    assert res["ceiling_applied"] is False
    assert 50.0 <= res["live_human_confidence"] <= 75.0


# ── TEST E: PHONE DISPLAYING FACE -> PRESENTATION ATTACK -> CONFIDENCE = 0 ─────
def test_rule_test_e_phone_displaying_face_zero_confidence():
    """
    TEST E:
    Phone detected + face associated inside the phone screen + high presentation confidence.
    Expectation: Live human direct-observation confidence = 0.0%, assessment POSSIBLE_SCREEN_REPLAY_ATTACK.
    """
    engine = ConfidenceFusionEngine()
    session_id = "test_e_session"

    # Even if person on screen is blinking!
    blink_res = {
        "blink_count": 2,
        "blink_quality": 0.95,
        "is_timer_paused": False,
        "challenge": {"active": False, "status": None},
    }
    eye_res = {
        "left_eye_visible": True,
        "right_eye_visible": True,
        "is_blurry": False,
        "eye_status": BOTH_EYES_VISIBLE,
        "overall_eye_quality": 0.90,
    }
    screen_res = {
        "phone_detected": True,
        "screen_face_associated": True,
        "presentation_attack": True,
        "presentation_attack_confidence": 0.92,
        "presentation_risk": 0.92,
    }
    movement_data = {
        "displacement_rate": 0.02,
        "d_yaw": 0.01,
        "d_pitch": 0.01,
        "pose_continuity": 0.85,
        "physiological_liveness": 0.80,
    }
    quality = {"quality_index": 78}
    benchmarks = {"faceforensics": {"score": 0.05}}

    res = engine.fuse(
        session_id=session_id,
        blink_res=blink_res,
        eye_res=eye_res,
        screen_res=screen_res,
        movement_data=movement_data,
        quality=quality,
        benchmarks=benchmarks,
    )

    assert res["presentation_attack_override"] is True
    assert res["live_human_confidence"] == 0.0
    assert res["model_probability"] == 0.0
    assert res["assessment"] == "POSSIBLE_SCREEN_REPLAY_ATTACK"


# ── TEST F: PHONE IN BACKGROUND -> NO CONFIDENCE OVERRIDE ──────────────────────
def test_rule_test_f_phone_in_background_no_override():
    """
    TEST F:
    Phone detected in background or held in hand, BUT face is NOT inside the phone screen.
    Expectation: No presentation override, normal evaluation continues.
    """
    engine = ConfidenceFusionEngine()
    session_id = "test_f_session"

    blink_res = {
        "blink_count": 1,
        "blink_quality": 0.85,
        "is_timer_paused": False,
        "challenge": {"active": False, "status": None},
    }
    eye_res = {
        "left_eye_visible": True,
        "right_eye_visible": True,
        "is_blurry": False,
        "eye_status": BOTH_EYES_VISIBLE,
        "overall_eye_quality": 0.85,
    }
    screen_res = {
        "phone_detected": True,
        "screen_face_associated": False,  # Phone is elsewhere in room/desk
        "presentation_attack": False,
        "presentation_attack_confidence": 0.20,
        "presentation_risk": 0.05,
    }
    movement_data = {
        "displacement_rate": 0.04,
        "d_yaw": 0.02,
        "d_pitch": 0.01,
        "pose_continuity": 0.92,
        "physiological_liveness": 0.85,
    }
    quality = {"quality_index": 75}
    benchmarks = {"faceforensics": {"score": 0.05}}

    res = engine.fuse(
        session_id=session_id,
        blink_res=blink_res,
        eye_res=eye_res,
        screen_res=screen_res,
        movement_data=movement_data,
        quality=quality,
        benchmarks=benchmarks,
    )

    assert res["presentation_attack_override"] is False
    assert res["live_human_confidence"] >= 65.0
    assert res["assessment"] == "LIKELY_LIVE_HUMAN"


# ── TEST G: ONE BLINK + HIGH REPLAY/SYNTHETIC RISK -> REPLAY DOMINATES ─────────
def test_rule_test_g_one_blink_high_replay_risk_dominates():
    """
    TEST G:
    Blink observed, but high frequency/replay risk or synthetic risk exists.
    Expectation: Disagreement flag is HIGH, reliability drops, assessment becomes SUSPICIOUS.
    """
    engine = ConfidenceFusionEngine()
    session_id = "test_g_session"

    blink_res = {
        "blink_count": 1,
        "blink_quality": 0.80,
        "is_timer_paused": False,
        "challenge": {"active": False, "status": None},
    }
    eye_res = {
        "left_eye_visible": True,
        "right_eye_visible": True,
        "is_blurry": False,
        "eye_status": BOTH_EYES_VISIBLE,
        "overall_eye_quality": 0.80,
    }
    # Strong Moiré patterns or synthetic artifact
    screen_res = {
        "phone_detected": False,
        "screen_face_associated": False,
        "presentation_attack": False,
        "presentation_attack_confidence": 0.30,
        "presentation_risk": 0.82,  # Severe Moiré
    }
    movement_data = {
        "displacement_rate": 0.03,
        "d_yaw": 0.01,
        "d_pitch": 0.01,
        "pose_continuity": 0.85,
        "physiological_liveness": 0.50,
    }
    quality = {"quality_index": 70}
    benchmarks = {"faceforensics": {"score": 0.80}}

    res = engine.fuse(
        session_id=session_id,
        blink_res=blink_res,
        eye_res=eye_res,
        screen_res=screen_res,
        movement_data=movement_data,
        quality=quality,
        benchmarks=benchmarks,
    )

    assert res["model_disagreement"] == "HIGH"
    assert res["reliability"] == "LOW"
    assert res["assessment"] == "SUSPICIOUS"


# ── TEST H: 4-STAGE BLINK STATE MACHINE (SINGLE-FRAME GLITCH PROTECTION) ───────
def test_blink_state_machine_rejects_single_frame_glitch():
    """
    A single frame dropout where openness drops for 1 frame must NOT be counted as a valid blink.
    Must observe OPEN -> CLOSING -> CLOSED -> OPEN over biological duration.
    """
    engine = BlinkEngine()
    session_id = "glitch_test_session"

    eye_analysis = {
        "overall_eye_quality": 0.85,
        "left_eye_visible": True,
        "right_eye_visible": True,
        "is_blurry": False,
        "is_obscured": False,
    }

    # Frame 1: Open
    r1 = engine.update(session_id, openness=22.0, eye_analysis=eye_analysis, face_detected=True)
    assert r1["blink_count"] == 0

    # Frame 2: Instant drop for 1 frame (e.g. tracking glitch)
    r2 = engine.update(session_id, openness=2.0, eye_analysis=eye_analysis, face_detected=True)
    assert r2["blink_count"] == 0

    # Frame 3: Instant reopen (total duration < 80ms)
    r3 = engine.update(session_id, openness=22.0, eye_analysis=eye_analysis, face_detected=True)
    assert r3["blink_count"] == 0
    assert r3["just_blinked"] is False


# ── TEST I: ONE EYE ONLY (PARTIAL VISIBILITY MULTIPLIER) ────────────────────────
def test_one_eye_only_partial_penalty():
    """
    If only one eye is visible (e.g. 3/4 angle), blink is still tracked but scaled by 0.75x.
    """
    engine = ConfidenceFusionEngine()
    session_id = "one_eye_session"

    res = engine.calculate_blink_evidence(
        blink_count=1,
        blink_quality=0.85,
        eye_status=LEFT_ONLY,
        left_eye_visible=True,
        right_eye_visible=False,
        is_eye_blurry=False,
    )

    assert res["blink_confirmed"] is True
    assert res["single_eye_penalty_applied"] is True
    # Base without penalty would be ~72-76; with 0.75x it should be ~54-58
    assert res["blink_evidence_score"] < 62.0


# ── TEST J: MULTIPLE BLINKS DIMINISHING RETURNS ─────────────────────────────────
def test_multiple_blinks_diminishing_returns():
    """
    1st blink gives major boost into 65-80.
    2nd blink adds modest boost (+5%).
    3rd blink adds tiny boost (+2%).
    Further blinks saturate.
    """
    engine = ConfidenceFusionEngine()

    ev1 = engine.calculate_blink_evidence(1, 0.85, BOTH_EYES_VISIBLE, True, True, False)
    ev2 = engine.calculate_blink_evidence(2, 0.85, BOTH_EYES_VISIBLE, True, True, False)
    ev3 = engine.calculate_blink_evidence(3, 0.85, BOTH_EYES_VISIBLE, True, True, False)
    ev4 = engine.calculate_blink_evidence(4, 0.85, BOTH_EYES_VISIBLE, True, True, False)

    score1 = ev1["blink_evidence_score"]
    score2 = ev2["blink_evidence_score"]
    score3 = ev3["blink_evidence_score"]
    score4 = ev4["blink_evidence_score"]

    assert score1 >= 65.0
    assert score2 > score1
    assert (score2 - score1) == pytest.approx(5.0, abs=0.5)
    assert (score3 - score2) == pytest.approx(2.0, abs=0.5)
    assert score4 == pytest.approx(score3, abs=0.5)
