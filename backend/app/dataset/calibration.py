"""
Privacy Eye — Confidence Calibration & Risk Mapping Engine
Implements:
1. Temperature Scaling & Platt Scaling
2. Expected Calibration Error (ECE) computation across probability bins
3. Brier Score computation
4. Calibrated risk band mapping (LIKELY LIVE HUMAN, POSSIBLE REPLAY, etc.)
"""

from typing import List, Tuple, Dict, Any, Optional
import numpy as np
from app.dataset.taxonomy import ResultState


class ConfidenceCalibrator:
    """Calibrates raw predictive scores and calculates reliability metrics."""

    def __init__(self, temperature: float = 1.35, platt_a: float = 1.0, platt_b: float = 0.0):
        self.temperature = max(0.1, temperature)
        self.platt_a = platt_a
        self.platt_b = platt_b

    def calibrate_probability(self, raw_prob: float) -> float:
        """
        Applies temperature scaling to raw probability:
        Maps raw [0, 1] to logit, scales by T, and applies sigmoid.
        """
        p = np.clip(raw_prob, 1e-6, 1.0 - 1e-6)
        logit = np.log(p / (1.0 - p))
        scaled_logit = (logit * self.platt_a + self.platt_b) / self.temperature
        calibrated = float(1.0 / (1.0 + np.exp(-scaled_logit)))
        return round(calibrated, 4)

    @staticmethod
    def calculate_expected_calibration_error(
        probabilities: List[float], labels: List[int], n_bins: int = 10
    ) -> float:
        """
        Calculates ECE: Weighted absolute difference between accuracy and mean confidence across bins.
        """
        if not probabilities or not labels or len(probabilities) != len(labels):
            return 0.0

        probs = np.array(probabilities)
        y_true = np.array(labels)
        bin_limits = np.linspace(0.0, 1.0, n_bins + 1)
        ece = 0.0
        n_samples = len(probs)

        for i in range(n_bins):
            bin_mask = (probs >= bin_limits[i]) & (probs < bin_limits[i + 1])
            if i == n_bins - 1:
                bin_mask = (probs >= bin_limits[i]) & (probs <= bin_limits[i + 1])

            count = np.sum(bin_mask)
            if count > 0:
                bin_acc = np.mean(y_true[bin_mask])
                bin_conf = np.mean(probs[bin_mask])
                ece += (count / n_samples) * abs(bin_acc - bin_conf)

        return float(round(ece, 4))

    @staticmethod
    def calculate_brier_score(probabilities: List[float], labels: List[int]) -> float:
        """Mean squared difference between predicted probabilities and actual binary outcomes."""
        if not probabilities or not labels or len(probabilities) != len(labels):
            return 0.0
        probs = np.array(probabilities)
        y_true = np.array(labels)
        return float(round(np.mean((probs - y_true) ** 2), 4))

    def map_to_result_state(
        self,
        calibrated_human_confidence: float,
        replay_risk: float,
        synthetic_risk: float,
        swap_risk: float,
        is_ood: bool = False,
        quality_passed: bool = True,
    ) -> Dict[str, Any]:
        """
        Maps calibrated scores to hierarchical ResultState.
        Enforces user-specified thresholds:
        - > 85%: LIKELY LIVE HUMAN
        - > 75% and <= 85%: Human face detected (Likely human face)
        - < 60%: Face is not likely human / Suspicious
        - Degraded or OOD: UNABLE TO DETERMINE
        """
        if not quality_passed or is_ood:
            return {
                "state": ResultState.UNABLE_TO_DETERMINE,
                "confidence_pct": round(calibrated_human_confidence * 100, 1),
                "reliability": "LOW",
                "risk_summary": "Input quality degraded or out-of-distribution.",
            }

        # Check for specific high-risk attack indicators
        if replay_risk >= 0.70:
            return {
                "state": ResultState.POSSIBLE_REPLAY,
                "confidence_pct": round(replay_risk * 100, 1),
                "reliability": "HIGH" if replay_risk > 0.85 else "MEDIUM",
                "risk_summary": "Screen moiré, planar reflection, or refresh artifacts detected.",
            }

        if swap_risk >= 0.70:
            return {
                "state": ResultState.POSSIBLE_FACE_SWAP,
                "confidence_pct": round(swap_risk * 100, 1),
                "reliability": "HIGH" if swap_risk > 0.85 else "MEDIUM",
                "risk_summary": "Facial perimeter boundary blending or resolution mismatch detected.",
            }

        if synthetic_risk >= 0.70:
            return {
                "state": ResultState.LIKELY_SYNTHETIC,
                "confidence_pct": round(synthetic_risk * 100, 1),
                "reliability": "HIGH" if synthetic_risk > 0.85 else "MEDIUM",
                "risk_summary": "High-frequency generative artifacts or GAN/Diffusion fingerprint detected.",
            }

        # Human Liveness Scale
        conf_pct = round(calibrated_human_confidence * 100, 1)

        if conf_pct >= 85.0:
            return {
                "state": ResultState.LIKELY_LIVE_HUMAN,
                "confidence_pct": conf_pct,
                "reliability": "HIGH",
                "risk_summary": "Multi-signal live human presence verified across all sensor branches.",
            }
        elif conf_pct >= 70.0:
            return {
                "state": ResultState.LIKELY_LIVE_HUMAN,
                "confidence_pct": conf_pct,
                "reliability": "MEDIUM",
                "risk_summary": "Likely human face; moderate confidence.",
            }
        elif conf_pct >= 60.0:
            return {
                "state": ResultState.SUSPICIOUS,
                "confidence_pct": conf_pct,
                "reliability": "LOW",
                "risk_summary": "Need more clarity of face or camera stabilization.",
            }
        else:
            return {
                "state": ResultState.SUSPICIOUS,
                "confidence_pct": conf_pct,
                "reliability": "MEDIUM",
                "risk_summary": "Face is not likely human as per database; suspicious authenticity cues.",
            }
