"""
Privacy Eye — Quality Gate & Input Pre-Validation Module
Calculates face size, sharpness, lighting, exposure, and motion blur before heavy inference.
Enforces the safety principle: Abstain with UNABLE TO DETERMINE on degraded inputs
rather than producing false certainty.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Tuple
import numpy as np
import cv2
from app.dataset.taxonomy import ResultState


@dataclass
class QualityResult:
    """Pre-inference input quality metrics and pass/fail assessment."""
    passed: bool
    overall_quality_score: float  # 0.0 to 1.0
    quality_label: str            # "EXCELLENT", "GOOD", "MARGINAL", "POOR", "UNUSABLE"
    sharpness_score: float        # Laplacian variance
    mean_luminance: float         # 0 to 255
    overexposed_ratio: float      # % of pixels > 245
    underexposed_ratio: float     # % of pixels < 15
    face_resolution: Tuple[int, int]
    motion_blur_detected: bool
    rejection_reasons: List[str] = field(default_factory=list)
    recommended_guidance: Optional[str] = None


class QualityGate:
    """Evaluates optical and geometric quality of incoming video frames."""

    MIN_FACE_WIDTH = 64
    MIN_FACE_HEIGHT = 64
    MIN_SHARPNESS_LAPLACIAN = 35.0
    MIN_MEAN_LUMINANCE = 30.0   # Lower is too dark
    MAX_MEAN_LUMINANCE = 230.0  # Higher is washed out
    MAX_UNDEREXPOSED_RATIO = 0.40
    MAX_OVEREXPOSED_RATIO = 0.35

    def evaluate_face_crop(self, face_bgr: np.ndarray) -> QualityResult:
        """Evaluates whether a cropped face is suitable for forensic analysis."""
        reasons: List[str] = []
        guidance: List[str] = []

        if face_bgr is None or face_bgr.size == 0:
            return QualityResult(
                passed=False,
                overall_quality_score=0.0,
                quality_label="UNUSABLE",
                sharpness_score=0.0,
                mean_luminance=0.0,
                overexposed_ratio=1.0,
                underexposed_ratio=1.0,
                face_resolution=(0, 0),
                motion_blur_detected=True,
                rejection_reasons=["Empty or null image frame received."],
                recommended_guidance="Ensure camera is connected and unobstructed.",
            )

        h, w = face_bgr.shape[:2]

        # 1. Size & Resolution Check
        if w < self.MIN_FACE_WIDTH or h < self.MIN_FACE_HEIGHT:
            reasons.append(f"Face resolution too small ({w}x{h} px; minimum is {self.MIN_FACE_WIDTH}x{self.MIN_FACE_HEIGHT} px)")
            guidance.append("Move closer to the camera.")

        # 2. Sharpness / Blur Check (Variance of Laplacian)
        gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        motion_blur = False
        if laplacian_var < self.MIN_SHARPNESS_LAPLACIAN:
            motion_blur = True
            reasons.append(f"Excessive motion blur or out-of-focus optics (Sharpness: {laplacian_var:.1f})")
            guidance.append("Hold still and ensure your camera is in focus.")

        # 3. Lighting & Exposure Check
        mean_lum = float(np.mean(gray))
        total_pixels = float(h * w)
        under_ratio = float(np.sum(gray < 15)) / total_pixels
        over_ratio = float(np.sum(gray > 245)) / total_pixels

        if mean_lum < self.MIN_MEAN_LUMINANCE or under_ratio > self.MAX_UNDEREXPOSED_RATIO:
            reasons.append(f"Insufficient illumination / severe underexposure (Mean luminance: {mean_lum:.1f}/255)")
            guidance.append("Improve room lighting or turn towards a light source.")

        if mean_lum > self.MAX_MEAN_LUMINANCE or over_ratio > self.MAX_OVEREXPOSED_RATIO:
            reasons.append(f"Severe overexposure or backlight glare (Overexposed: {over_ratio*100:.1f}%)")
            guidance.append("Reduce harsh backlight behind you or lower exposure.")

        # 4. Compute overall quality score (0.0 to 1.0)
        norm_sharpness = min(1.0, laplacian_var / 200.0)
        norm_lum = 1.0 - abs(mean_lum - 128.0) / 128.0
        norm_size = min(1.0, (w * h) / (256.0 * 256.0))
        quality_score = float(np.clip(0.40 * norm_sharpness + 0.35 * norm_lum + 0.25 * norm_size, 0.0, 1.0))

        if quality_score >= 0.80:
            quality_label = "EXCELLENT"
        elif quality_score >= 0.60:
            quality_label = "GOOD"
        elif quality_score >= 0.40:
            quality_label = "MARGINAL"
        elif quality_score >= 0.20:
            quality_label = "POOR"
        else:
            quality_label = "UNUSABLE"

        passed = len(reasons) == 0

        user_guidance_str = " ".join(guidance) if guidance else None

        return QualityResult(
            passed=passed,
            overall_quality_score=round(quality_score, 3),
            quality_label=quality_label,
            sharpness_score=round(laplacian_var, 1),
            mean_luminance=round(mean_lum, 1),
            overexposed_ratio=round(over_ratio, 3),
            underexposed_ratio=round(under_ratio, 3),
            face_resolution=(w, h),
            motion_blur_detected=motion_blur,
            rejection_reasons=reasons,
            recommended_guidance=user_guidance_str,
        )
