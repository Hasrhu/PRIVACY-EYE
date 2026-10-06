"""
Privacy Eye — Part 12: Quantitative Blink Model Evaluation Suite
Measures Event Precision, Recall, F1 Score, False Blink Rate (FBR), Missed Blink Rate (MBR),
Duplicate Blink Rate, and Processing Latency on unseen test subjects across diverse FPS conditions.
"""
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
import numpy as np

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "backend"))
sys.path.insert(0, str(ROOT_DIR))

from ml.datasets.blink_dataset import BlinkDatasetGenerator
from app.ml.blink_detection.blink_state_machine import TemporalBlinkStateMachine
from app.ml.blink_detection.temporal_model import TemporalBlinkClassifier


def evaluate_test_set() -> Dict[str, Any]:
    print("=" * 68)
    print("PRIVACY EYE — QUANTITATIVE EYE & BLINK EVALUATION REPORT")
    print("=" * 68)

    # 1. Load Model
    model = TemporalBlinkClassifier()
    weights_path = ROOT_DIR / "ml" / "models" / "blink_temporal_model.npz"
    if weights_path.exists():
        model.load_weights(str(weights_path))
        print(f"Loaded trained checkpoint: {weights_path}")
    else:
        print("[WARN] Model weights not found, using initialized weights")

    # 2. Build Unseen Test Split (8 subjects, 56 sequences)
    gen = BlinkDatasetGenerator(seed=42)
    _, _, test_seqs = gen.build_dataset_splits(num_subjects=50)
    print(f"Evaluating across {len(test_seqs)} unseen test sequences (Subjects 43-50)...")

    true_positives = 0
    false_positives = 0
    false_negatives = 0
    duplicate_blinks = 0
    total_frames_processed = 0
    latencies_ms = []

    for seq in test_seqs:
        # Create fresh state machine instance per test sequence
        sm = TemporalBlinkStateMachine(temporal_classifier=model)
        sess_id = seq.sequence_id
        ground_truth_blinks = seq.blink_count
        detected_blinks = 0

        for frame in seq.frames:
            # Build mock eye_data from frame ground truth
            is_vis = (frame.eye_visibility != "UNKNOWN")
            eye_data = {
                "eye_visibility_state": "BOTH_VISIBLE" if is_vis else "NONE_VISIBLE",
                "overall_eye_quality": frame.quality if is_vis else 0.15,
                "is_blurry": not is_vis,
                "is_obscured": False,
                "mean_ear": frame.mean_ear,
                "left_ear": frame.left_ear,
                "right_ear": frame.right_ear,
                "left_eye": {
                    "visible": frame.left_eye_visible and is_vis,
                    "quality": frame.quality if is_vis else 0.15,
                    "ear": frame.left_ear,
                },
                "right_eye": {
                    "visible": frame.right_eye_visible and is_vis,
                    "quality": frame.quality if is_vis else 0.15,
                    "ear": frame.right_ear,
                },
            }

            t0 = time.perf_counter()
            res = sm.update(
                session_id=sess_id,
                eye_data=eye_data,
                face_detected=True,
                head_pose={"yaw": frame.head_yaw, "pitch": frame.head_pitch},
                timestamp_ms=frame.timestamp_ms,
            )
            lat_ms = (time.perf_counter() - t0) * 1000.0
            latencies_ms.append(lat_ms)
            total_frames_processed += 1

            if res["just_blinked"]:
                detected_blinks += 1

        # Evaluate sequence event outcome
        if ground_truth_blinks >= 1:
            if detected_blinks == ground_truth_blinks:
                true_positives += ground_truth_blinks
            elif detected_blinks > ground_truth_blinks:
                true_positives += ground_truth_blinks
                duplicate_blinks += (detected_blinks - ground_truth_blinks)
            else:
                true_positives += detected_blinks
                false_negatives += (ground_truth_blinks - detected_blinks)
                print(f"  [MISS] Scenario: {seq.scenario_type} at {seq.fps} FPS ({seq.subject_id}) - detected {detected_blinks}/{ground_truth_blinks}")
        elif ground_truth_blinks == 0:
            if detected_blinks > 0:
                false_positives += detected_blinks
                print(f"  [FALSE POSITIVE] Scenario: {seq.scenario_type} at {seq.fps} FPS ({seq.subject_id}) - detected {detected_blinks}")

    # 3. Calculate Performance Metrics
    total_ground_truth_blinks = sum(s.blink_count for s in test_seqs)
    total_detected_events = true_positives + false_positives

    precision = true_positives / max(1, total_detected_events)
    recall = true_positives / max(1, total_ground_truth_blinks)
    f1 = 2 * (precision * recall) / max(1e-6, (precision + recall))

    false_blink_rate = false_positives / max(1, total_detected_events)
    missed_blink_rate = false_negatives / max(1, total_ground_truth_blinks)
    duplicate_blink_rate = duplicate_blinks / max(1, total_detected_events)

    avg_latency = float(np.mean(latencies_ms))
    p95_latency = float(np.percentile(latencies_ms, 95))
    throughput_fps = 1000.0 / max(1e-3, avg_latency)

    # Calculate events per minute
    total_video_seconds = sum(len(s.frames) / s.fps for s in test_seqs)
    total_video_minutes = total_video_seconds / 60.0
    false_blinks_per_min = false_positives / max(0.1, total_video_minutes)
    missed_blinks_per_min = false_negatives / max(0.1, total_video_minutes)

    print("-" * 68)
    print("MEASURED TEST SET PERFORMANCE:")
    print(f"  * Total Sequences Evaluated:     {len(test_seqs)}")
    print(f"  * Total Frames Processed:        {total_frames_processed}")
    print(f"  * True Physical Blinks:          {total_ground_truth_blinks}")
    print(f"  * Correctly Detected Blinks:     {true_positives}")
    print(f"  * False Blinks Flagged:          {false_positives}")
    print(f"  * Missed Blinks:                 {false_negatives}")
    print(f"  * Duplicate Blinks:              {duplicate_blinks}")
    print("-" * 68)
    print(f"  * Blink Event Precision:         {precision * 100:.2f}%")
    print(f"  * Blink Event Recall:            {recall * 100:.2f}%")
    print(f"  * F1 Score:                      {f1 * 100:.2f}%")
    print(f"  * False Blink Rate (FBR):        {false_blink_rate * 100:.2f}%")
    print(f"  * Missed Blink Rate (MBR):       {missed_blink_rate * 100:.2f}%")
    print(f"  * Duplicate Blink Rate:          {duplicate_blink_rate * 100:.2f}%")
    print(f"  * False Blinks per Minute:       {false_blinks_per_min:.2f} / min")
    print(f"  * Missed Blinks per Minute:      {missed_blinks_per_min:.2f} / min")
    print("-" * 68)
    print("SPEED & LATENCY PERFORMANCE:")
    print(f"  * Average Latency:               {avg_latency:.3f} ms / frame")
    print(f"  * 95th Percentile Latency:       {p95_latency:.3f} ms / frame")
    print(f"  * Processing Throughput:         {throughput_fps:.1f} FPS (Target: >= 30 FPS)")
    print("=" * 68)

    return {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "false_blink_rate": round(false_blink_rate, 4),
        "missed_blink_rate": round(missed_blink_rate, 4),
        "duplicate_blink_rate": round(duplicate_blink_rate, 4),
        "avg_latency_ms": round(avg_latency, 3),
        "throughput_fps": round(throughput_fps, 1),
    }


if __name__ == "__main__":
    evaluate_test_set()
