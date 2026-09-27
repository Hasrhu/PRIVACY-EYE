"""
Privacy Eye — Test Suite for Dataset Governance, Splitting, Augmentation, Quality Gate, and Calibration
Compatible with standard Python unittest.
"""

import unittest
import numpy as np
import cv2

from app.dataset.taxonomy import (
    DatasetCategory,
    DatasetSampleMetadata,
    SplitType,
    GeneratorFamily,
    DeviceClass,
    EnvironmentType,
    ResultState,
)
from app.dataset.splitter import DatasetSplitter
from app.dataset.augmentation import ProbabilisticAugmentor
from app.dataset.quality_gate import QualityGate
from app.dataset.ood_detector import OODDetector
from app.dataset.calibration import ConfidenceCalibrator
from app.dataset.failure_mining import FailureCaseManager


class TestDatasetSystem(unittest.TestCase):

    def test_subject_disjoint_splitting(self):
        """Verify that train, val, and test partitions contain ZERO overlapping subjects."""
        samples = []
        # 20 distinct subjects, 5 samples each = 100 samples
        for i in range(20):
            subj_id = f"person_{i:03d}"
            for j in range(5):
                s = DatasetSampleMetadata(
                    sample_id=f"{subj_id}_rec_{j}",
                    category=DatasetCategory.CATEGORY_A_GENUINE,
                    source_dataset="InternalConsented",
                    license_terms="InternalConsent-v1",
                    subject_id=subj_id,
                    video_id=f"vid_{i}_{j}",
                )
                samples.append(s)

        splitter = DatasetSplitter(train_ratio=0.70, val_ratio=0.15, test_ratio=0.15, seed=42)
        splits = splitter.split_subject_disjoint(samples)

        train_subjects = {s.subject_id for s in splits[SplitType.TRAIN]}
        val_subjects = {s.subject_id for s in splits[SplitType.VAL]}
        test_subjects = {s.subject_id for s in splits[SplitType.TEST_UNSEEN_SUBJECT]}

        self.assertTrue(len(train_subjects) > 0)
        self.assertTrue(len(val_subjects) > 0)
        self.assertTrue(len(test_subjects) > 0)

        # Strict isolation checks
        self.assertTrue(train_subjects.isdisjoint(val_subjects), "Data Leakage: Train and Val subjects overlap!")
        self.assertTrue(train_subjects.isdisjoint(test_subjects), "Data Leakage: Train and Test subjects overlap!")
        self.assertTrue(val_subjects.isdisjoint(test_subjects), "Data Leakage: Val and Test subjects overlap!")

    def test_generator_disjoint_splitting(self):
        """Verify unseen generator samples are strictly segregated into held-out evaluation."""
        generators = [
            GeneratorFamily.STYLEGAN2,
            GeneratorFamily.PROGAN,
            GeneratorFamily.STABLE_DIFFUSION_15,
            GeneratorFamily.FLUX_1,
            GeneratorFamily.SDXL,
        ]
        samples = []
        for idx, gen in enumerate(generators):
            for k in range(4):
                samples.append(
                    DatasetSampleMetadata(
                        sample_id=f"synth_{idx}_{k}",
                        category=DatasetCategory.CATEGORY_B_SYNTHETIC,
                        source_dataset="GenBench",
                        license_terms="ResearchOnly",
                        generator=gen,
                    )
                )

        splitter = DatasetSplitter()
        held_out = {GeneratorFamily.FLUX_1, GeneratorFamily.SDXL}
        seen, unseen = splitter.create_generator_disjoint_split(samples, held_out)

        self.assertEqual(len(unseen), 8)  # 4 FLUX_1 + 4 SDXL
        self.assertEqual(len(seen), 12)
        for item in unseen:
            self.assertIn(item.generator, held_out)
            self.assertEqual(item.split, SplitType.TEST_UNSEEN_GENERATOR)
        for item in seen:
            self.assertNotIn(item.generator, held_out)

    def test_probabilistic_augmentation(self):
        """Verify augmentation preserves format, valid uint8 values, and non-empty sequences."""
        augmentor = ProbabilisticAugmentor(seed=123)
        dummy_face = np.full((128, 128, 3), 120, dtype=np.uint8)
        cv2.circle(dummy_face, (64, 64), 30, (200, 200, 200), -1)

        augmented_img = augmentor.augment_image(dummy_face)
        self.assertEqual(augmented_img.shape, (128, 128, 3))
        self.assertEqual(augmented_img.dtype, np.uint8)

        seq = [dummy_face.copy() for _ in range(10)]
        augmented_seq = augmentor.augment_video_sequence(seq)
        self.assertTrue(len(augmented_seq) > 0)
        self.assertEqual(augmented_seq[0].shape, (128, 128, 3))

    def test_quality_gate_abstention_and_acceptance(self):
        """Verify quality gate rejects degraded inputs and accepts clean faces."""
        qgate = QualityGate()

        # 1. Null / Tiny face crop
        tiny_crop = np.zeros((32, 32, 3), dtype=np.uint8)
        res_tiny = qgate.evaluate_face_crop(tiny_crop)
        self.assertFalse(res_tiny.passed)
        self.assertTrue(any("too small" in r for r in res_tiny.rejection_reasons))

        # 2. Extreme dark / underexposed crop
        dark_crop = np.full((128, 128, 3), 5, dtype=np.uint8)
        res_dark = qgate.evaluate_face_crop(dark_crop)
        self.assertFalse(res_dark.passed)
        self.assertTrue(any("Insufficient illumination" in r for r in res_dark.rejection_reasons))

        # 3. High quality synthetic face crop
        clean_crop = np.full((160, 160, 3), 130, dtype=np.uint8)
        cv2.rectangle(clean_crop, (20, 20), (140, 140), (40, 60, 200), 2)
        cv2.circle(clean_crop, (50, 60), 10, (20, 20, 20), -1)
        cv2.circle(clean_crop, (110, 60), 10, (20, 20, 20), -1)
        cv2.ellipse(clean_crop, (80, 110), (30, 15), 0, 0, 180, (20, 20, 20), 2)

        res_clean = qgate.evaluate_face_crop(clean_crop)
        self.assertTrue(res_clean.passed)
        self.assertGreaterEqual(res_clean.overall_quality_score, 0.40)
        self.assertEqual(len(res_clean.rejection_reasons), 0)

    def test_ood_detector_energy_and_disagreement(self):
        """Verify OOD detector flags divergent signals as UNABLE TO DETERMINE."""
        ood = OODDetector(energy_threshold=-1.5, disagreement_threshold=0.30)

        # In-distribution logits (high confidence in one class)
        id_logits = np.array([5.0, 0.2, 0.1])
        id_branches = [0.85, 0.88, 0.82]
        eval_id = ood.evaluate_sample(id_logits, id_branches)
        self.assertFalse(eval_id["is_ood"])
        self.assertEqual(eval_id["recommended_state"], "IN_DISTRIBUTION")

        # Conflicting branches (e.g. Branch 1 says Real 0.95, Branch 2 says Fake 0.10)
        conflict_branches = [0.95, 0.10, 0.80, 0.15]
        eval_conflict = ood.evaluate_sample(id_logits, conflict_branches)
        self.assertTrue(eval_conflict["is_ood"])
        self.assertEqual(eval_conflict["recommended_state"], "UNABLE TO DETERMINE")

    def test_confidence_calibrator_and_ece(self):
        """Verify temperature scaling, ECE calculation, and result state mapping."""
        calibrator = ConfidenceCalibrator(temperature=1.2)

        p_raw = 0.95
        p_cal = calibrator.calibrate_probability(p_raw)
        self.assertTrue(0.0 < p_cal < 1.0)

        # ECE test with perfect calibration
        probs = [0.1, 0.2, 0.8, 0.9]
        labels = [0, 0, 1, 1]
        ece = ConfidenceCalibrator.calculate_expected_calibration_error(probs, labels, n_bins=2)
        self.assertGreaterEqual(ece, 0.0)

        # Decision mapping
        state_high = calibrator.map_to_result_state(
            calibrated_human_confidence=0.92,
            replay_risk=0.1,
            synthetic_risk=0.05,
            swap_risk=0.05,
        )
        self.assertEqual(state_high["state"], ResultState.LIKELY_LIVE_HUMAN)
        self.assertGreaterEqual(state_high["confidence_pct"], 85.0)

        state_replay = calibrator.map_to_result_state(
            calibrated_human_confidence=0.40,
            replay_risk=0.88,
            synthetic_risk=0.1,
            swap_risk=0.1,
        )
        self.assertEqual(state_replay["state"], ResultState.POSSIBLE_REPLAY)

    def test_failure_mining_manager(self):
        """Verify logging failure cases and mining high-confidence mistakes."""
        manager = FailureCaseManager()
        manager.log_failure(
            model_version="v1.4",
            input_type="image",
            device="cheap_webcam",
            resolution="480p",
            environment="dim_bedroom",
            true_label="real",
            prediction="LIKELY SYNTHETIC",
            confidence=0.89,  # High confidence mistake!
            reason="Sensor noise resembled GAN upsampling artifacts",
        )
        manager.log_failure(
            model_version="v1.4",
            input_type="image",
            device="mac_hd",
            resolution="720p",
            environment="bright_office",
            true_label="real",
            prediction="real",
            confidence=0.91,
            reason="Correct",
        )

        mistakes = manager.get_high_confidence_mistakes(confidence_threshold=0.80)
        self.assertEqual(len(mistakes), 1)
        self.assertEqual(mistakes[0].confidence, 0.89)
        self.assertEqual(mistakes[0].true_label, "real")

        # Human approval
        approved = manager.review_and_approve(mistakes[0].failure_id, reviewer_id="researcher_alice")
        self.assertTrue(approved.is_verified_by_human)
        self.assertTrue(approved.added_to_training_set)


if __name__ == "__main__":
    unittest.main()
