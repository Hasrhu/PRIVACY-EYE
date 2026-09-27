"""
Privacy Eye — Failure Case Management & Hard-Negative Mining Pipeline
Maintains failure records, filters high-confidence mistakes, and orchestrates
the human-in-the-loop review workflow before adding validated edge cases to the dataset.
"""

from typing import List, Dict, Any, Optional
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict


@dataclass
class FailureCaseRecord:
    failure_id: str
    model_version: str
    input_type: str        # "image", "video_frame", "temporal_sequence"
    device: str
    resolution: str
    environment: str
    true_label: str        # e.g. "real"
    prediction: str        # e.g. "LIKELY SYNTHETIC"
    confidence: float      # e.g. 0.88 (high-confidence mistake)
    reason: str            # e.g. "webcam sensor noise mistaken for GAN grid"
    reviewed_by: Optional[str] = None
    is_verified_by_human: bool = False
    added_to_training_set: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class FailureCaseManager:
    """Manages failure cases and isolates candidate hard-negatives for retraining."""

    def __init__(self):
        # In-memory store (also persisted to PostgreSQL failure_cases table)
        self._records: Dict[str, FailureCaseRecord] = {}

    def log_failure(
        self,
        model_version: str,
        input_type: str,
        device: str,
        resolution: str,
        environment: str,
        true_label: str,
        prediction: str,
        confidence: float,
        reason: str,
    ) -> FailureCaseRecord:
        """Logs an authenticated model failure for investigation."""
        rec = FailureCaseRecord(
            failure_id=f"fail_{uuid.uuid4().hex[:12]}",
            model_version=model_version,
            input_type=input_type,
            device=device,
            resolution=resolution,
            environment=environment,
            true_label=true_label,
            prediction=prediction,
            confidence=round(confidence, 4),
            reason=reason,
        )
        self._records[rec.failure_id] = rec
        return rec

    def get_high_confidence_mistakes(self, confidence_threshold: float = 0.75) -> List[FailureCaseRecord]:
        """
        Extracts worst-case mistakes: where model made a wrong prediction with high confidence.
        These are the most critical samples for hard-negative retraining.
        """
        mistakes = []
        for rec in self._records.values():
            if rec.true_label.lower() not in rec.prediction.lower() and rec.confidence >= confidence_threshold:
                mistakes.append(rec)
        return sorted(mistakes, key=lambda x: x.confidence, reverse=True)

    def review_and_approve(
        self, failure_id: str, reviewer_id: str, add_to_dataset: bool = True
    ) -> Optional[FailureCaseRecord]:
        """Human-in-the-loop review approval before promotion to dataset."""
        if failure_id not in self._records:
            return None
        rec = self._records[failure_id]
        rec.reviewed_by = reviewer_id
        rec.is_verified_by_human = True
        rec.added_to_training_set = add_to_dataset
        return rec

    def list_all(self) -> List[Dict[str, Any]]:
        return [asdict(r) for r in self._records.values()]
