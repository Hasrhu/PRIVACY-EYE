"""
Privacy Eye — Dataset Leakage Prevention & Split Verification Tool
Phase 9 Deliverable: Fails loudly if subjects, source videos, or held-out test generators leak across splits.
"""

import sys
import os
import csv
from typing import Dict, Set, List


def check_dataset_leakage(manifest_path: str) -> bool:
    if not os.path.exists(manifest_path):
        print(f"[ERROR] Manifest file not found: {manifest_path}")
        return False

    splits_subjects: Dict[str, Set[str]] = {}
    splits_videos: Dict[str, Set[str]] = {}
    splits_generators: Dict[str, Set[str]] = {}

    row_count = 0
    with open(manifest_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_count += 1
            split = row.get("split", "train").strip()
            subject_id = row.get("subject_id", "").strip()
            video_id = row.get("source_video_id", "").strip()
            generator = row.get("generator", "").strip()

            if split not in splits_subjects:
                splits_subjects[split] = set()
                splits_videos[split] = set()
                splits_generators[split] = set()

            if subject_id and subject_id.lower() != "none":
                splits_subjects[split].add(subject_id)
            if video_id and video_id.lower() != "none":
                splits_videos[split].add(video_id)
            if generator and generator.lower() != "none":
                splits_generators[split].add(generator)

    print("=" * 65)
    print("PRIVACY EYE — DATASET LEAKAGE AUDIT REPORT")
    print(f"Total manifest samples audited: {row_count}")
    print(f"Splits discovered: {list(splits_subjects.keys())}")
    print("=" * 65)

    leakage_detected = False

    # 1. Subject Disjoint Audit across Train, Val, and Test
    split_names = list(splits_subjects.keys())
    for i in range(len(split_names)):
        for j in range(i + 1, len(split_names)):
            s1, s2 = split_names[i], split_names[j]
            overlap_subjects = splits_subjects[s1].intersection(splits_subjects[s2])
            if overlap_subjects:
                print(f"[FATAL LEAKAGE] Overlapping subjects between '{s1}' and '{s2}': {overlap_subjects}")
                leakage_detected = True

            overlap_videos = splits_videos[s1].intersection(splits_videos[s2])
            if overlap_videos:
                print(f"[FATAL LEAKAGE] Overlapping source videos between '{s1}' and '{s2}': {overlap_videos}")
                leakage_detected = True

    # 2. Generator Disjoint Audit (Held-out generators in test_unseen_generator must NOT be in train)
    train_gens = splits_generators.get("train", set())
    unseen_test_gens = splits_generators.get("test_unseen_generator", set())
    overlap_gens = train_gens.intersection(unseen_test_gens)
    if overlap_gens:
        print(f"[FATAL LEAKAGE] Train and Unseen-Generator Test share identical generator families: {overlap_gens}")
        leakage_detected = True

    if leakage_detected:
        print("\n[VERDICT: FAILED] Data leakage detected! Rejecting dataset manifest.")
        return False
    else:
        print("\n[VERDICT: PASSED] 100% Subject-Disjoint, Video-Disjoint, and Generator-Disjoint isolation verified.")
        return True


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join("datasets", "manifest.csv")
    success = check_dataset_leakage(path)
    sys.exit(0 if success else 1)
