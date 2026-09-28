"""
Privacy Eye — Generator-Disjoint Evaluation Benchmark
Phase 8 Deliverable: Measures zero-shot cross-generator generalization on unseen synthesis families.
"""

from typing import Dict, Any, List, Set
import numpy as np


class GeneratorDisjointEvaluator:
    """Evaluates detector accuracy on unseen generative model families."""

    def __init__(self, seen_generators: Set[str], unseen_generators: Set[str]):
        self.seen_generators = {g.lower() for g in seen_generators}
        self.unseen_generators = {g.lower() for g in unseen_generators}

    def evaluate_predictions(
        self, samples: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculates separate metrics for:
        - Seen Generators (In-Distribution Synthesis)
        - Unseen Generators (Zero-Shot Cross-Generator Generalization)
        """
        seen_true = []
        seen_pred = []
        unseen_true = []
        unseen_pred = []

        for s in samples:
            gen = s.get("generator", "none").lower()
            true_label = 1 if s.get("label", "").lower() == "synthetic" else 0
            score = float(s.get("predicted_score", 0.5))

            if gen in self.seen_generators:
                seen_true.append(true_label)
                seen_pred.append(score)
            elif gen in self.unseen_generators:
                unseen_true.append(true_label)
                unseen_pred.append(score)

        def compute_metrics(y_true, y_scores, threshold=0.5):
            if not y_true:
                return {"accuracy": 0.0, "count": 0}
            preds = [1 if s >= threshold else 0 for s in y_scores]
            acc = float(np.mean([p == t for p, t in zip(preds, y_true)]))
            return {
                "count": len(y_true),
                "accuracy": round(acc, 4),
                "mean_score": round(float(np.mean(y_scores)), 4),
            }

        seen_metrics = compute_metrics(seen_true, seen_pred)
        unseen_metrics = compute_metrics(unseen_true, unseen_pred)

        # Generalization drop: drop in accuracy when evaluating on novel generators
        gen_drop = 0.0
        if seen_metrics["count"] > 0 and unseen_metrics["count"] > 0:
            gen_drop = round(seen_metrics["accuracy"] - unseen_metrics["accuracy"], 4)

        return {
            "seen_generators": list(self.seen_generators),
            "unseen_generators": list(self.unseen_generators),
            "seen_benchmark": seen_metrics,
            "unseen_benchmark": unseen_metrics,
            "generalization_drop": gen_drop,
            "passed_generalization_threshold": bool(gen_drop <= 0.12),
        }
