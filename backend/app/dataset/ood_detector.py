"""
Privacy Eye — Out-of-Distribution (OOD) & Open-Set Attack Detection
Identifies inputs that deviate significantly from known training distributions
(e.g., novel generative models, unseen physical masks, adversarial perturbations).
Triggers abstention state: UNABLE TO DETERMINE rather than forcing a high-risk misclassification.
"""

from typing import List, Tuple, Dict, Any, Optional
import numpy as np


class OODDetector:
    """Detects out-of-distribution inputs via Energy scores and Ensemble Disagreement."""

    def __init__(
        self,
        energy_threshold: float = -2.5,
        disagreement_threshold: float = 0.35,
        temperature: float = 1.0,
    ):
        self.energy_threshold = energy_threshold
        self.disagreement_threshold = disagreement_threshold
        self.temperature = temperature
        # Centroid and precision matrix for Mahalanobis estimation (bona fide reference cluster)
        self.reference_centroid: Optional[np.ndarray] = None
        self.reference_cov_inv: Optional[np.ndarray] = None

    def compute_energy_score(self, logits: np.ndarray) -> float:
        """
        Calculates Free Energy: E(x) = -T * log(sum(exp(logits / T)))
        High energy scores correspond to inputs that lie in low-density feature space regions.
        """
        scaled = np.array(logits, dtype=np.float64) / self.temperature
        # Numerical stability via max-subtraction
        max_val = np.max(scaled)
        logsumexp = max_val + np.log(np.sum(np.exp(scaled - max_val)))
        energy = -self.temperature * logsumexp
        return float(energy)

    def compute_ensemble_disagreement(self, branch_probabilities: List[float]) -> float:
        """
        Calculates epistemic uncertainty through variance among independent signal branches
        (e.g. Spatial, Temporal, Active Challenge, Replay).
        High disagreement indicates the model has never encountered this confluence of signals.
        """
        if not branch_probabilities or len(branch_probabilities) < 2:
            return 0.0
        return float(np.std(branch_probabilities))

    def evaluate_sample(
        self,
        logits: np.ndarray,
        branch_probabilities: List[float],
        embedding: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates whether an input is In-Distribution (ID) or Out-of-Distribution (OOD).
        Returns diagnostic metrics and abstention recommendation.
        """
        energy = self.compute_energy_score(logits)
        disagreement = self.compute_ensemble_disagreement(branch_probabilities)

        is_energy_ood = energy > self.energy_threshold
        is_disagreement_ood = disagreement > self.disagreement_threshold

        mahalanobis_dist = 0.0
        if embedding is not None and self.reference_centroid is not None and self.reference_cov_inv is not None:
            diff = embedding - self.reference_centroid
            mahalanobis_dist = float(np.sqrt(np.dot(np.dot(diff, self.reference_cov_inv), diff.T)))

        is_ood = is_energy_ood or is_disagreement_ood

        reasons = []
        if is_energy_ood:
            reasons.append(f"High free-energy divergence ({energy:.2f} > threshold {self.energy_threshold})")
        if is_disagreement_ood:
            reasons.append(f"High multi-signal branch disagreement ({disagreement:.2f} > threshold {self.disagreement_threshold})")

        return {
            "is_ood": is_ood,
            "energy_score": round(energy, 3),
            "ensemble_disagreement": round(disagreement, 3),
            "mahalanobis_distance": round(mahalanobis_dist, 3),
            "reasons": reasons,
            "recommended_state": "UNABLE TO DETERMINE" if is_ood else "IN_DISTRIBUTION",
        }
