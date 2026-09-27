"""
Privacy Eye — Dataset Splitter & Leakage Prevention Engine
Enforces:
1. Subject-Disjoint splits (Subjects never cross Train/Val/Test).
2. Video-Level Disjoint splits (Nearby frames from same video cannot leak across sets).
3. Generator-Disjoint splits (Unseen generators strictly held out for generalization benchmarks).
4. Device-Disjoint & Environment-Disjoint splits.
"""

from typing import List, Dict, Set, Tuple
import random
from app.dataset.taxonomy import (
    DatasetSampleMetadata,
    SplitType,
    GeneratorFamily,
    DeviceClass,
    EnvironmentType,
)


class DatasetSplitter:
    """Partitions dataset samples preventing identity, video, and generator leakage."""

    def __init__(
        self,
        train_ratio: float = 0.70,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        seed: int = 42,
    ):
        assert abs((train_ratio + val_ratio + test_ratio) - 1.0) < 1e-5, "Split ratios must sum to 1.0"
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.seed = seed

    def split_subject_disjoint(
        self, samples: List[DatasetSampleMetadata]
    ) -> Dict[SplitType, List[DatasetSampleMetadata]]:
        """
        Groups samples by subject_id (or video_id for synthetic/anonymous).
        Partitions unique subject IDs to ensure zero identity overlap.
        """
        rng = random.Random(self.seed)

        # 1. Group samples by primary entity (subject_id fallback to video_id fallback to sample_id)
        subject_to_samples: Dict[str, List[DatasetSampleMetadata]] = {}
        for s in samples:
            entity_key = s.subject_id or s.video_id or s.sample_id
            subject_to_samples.setdefault(entity_key, []).append(s)

        unique_subjects = list(subject_to_samples.keys())
        rng.shuffle(unique_subjects)

        total_subjects = len(unique_subjects)
        n_train = int(total_subjects * self.train_ratio)
        n_val = int(total_subjects * self.val_ratio)

        train_subjects = set(unique_subjects[:n_train])
        val_subjects = set(unique_subjects[n_train:n_train + n_val])
        test_subjects = set(unique_subjects[n_train + n_val:])

        # Verify absolute disjointness
        assert train_subjects.isdisjoint(val_subjects), "Data Leakage: Train and Val subjects overlap!"
        assert train_subjects.isdisjoint(test_subjects), "Data Leakage: Train and Test subjects overlap!"
        assert val_subjects.isdisjoint(test_subjects), "Data Leakage: Val and Test subjects overlap!"

        partitioned: Dict[SplitType, List[DatasetSampleMetadata]] = {
            SplitType.TRAIN: [],
            SplitType.VAL: [],
            SplitType.TEST_UNSEEN_SUBJECT: [],
        }

        for subj, items in subject_to_samples.items():
            if subj in train_subjects:
                for item in items:
                    item.split = SplitType.TRAIN
                partitioned[SplitType.TRAIN].extend(items)
            elif subj in val_subjects:
                for item in items:
                    item.split = SplitType.VAL
                partitioned[SplitType.VAL].extend(items)
            else:
                for item in items:
                    item.split = SplitType.TEST_UNSEEN_SUBJECT
                partitioned[SplitType.TEST_UNSEEN_SUBJECT].extend(items)

        return partitioned

    def create_generator_disjoint_split(
        self,
        samples: List[DatasetSampleMetadata],
        held_out_generators: Set[GeneratorFamily],
    ) -> Tuple[List[DatasetSampleMetadata], List[DatasetSampleMetadata]]:
        """
        Splits synthetic samples into Train/Val generators and Unseen Test generators.
        Example: Train on StyleGAN2 & SD 1.5; Test exclusively on FLUX.1 & SDXL.
        """
        seen_samples: List[DatasetSampleMetadata] = []
        unseen_test_samples: List[DatasetSampleMetadata] = []

        for sample in samples:
            if sample.generator in held_out_generators:
                sample.split = SplitType.TEST_UNSEEN_GENERATOR
                unseen_test_samples.append(sample)
            else:
                seen_samples.append(sample)

        return seen_samples, unseen_test_samples

    def create_device_disjoint_split(
        self,
        samples: List[DatasetSampleMetadata],
        held_out_devices: Set[DeviceClass],
    ) -> Tuple[List[DatasetSampleMetadata], List[DatasetSampleMetadata]]:
        """Separates known capture hardware from completely novel sensor tests."""
        train_samples: List[DatasetSampleMetadata] = []
        unseen_device_test: List[DatasetSampleMetadata] = []

        for s in samples:
            if s.device in held_out_devices:
                s.split = SplitType.TEST_UNSEEN_DEVICE
                unseen_device_test.append(s)
            else:
                train_samples.append(s)

        return train_samples, unseen_device_test

    def create_environment_disjoint_split(
        self,
        samples: List[DatasetSampleMetadata],
        held_out_environments: Set[EnvironmentType],
    ) -> Tuple[List[DatasetSampleMetadata], List[DatasetSampleMetadata]]:
        """Separates indoor lighting from outdoor / extreme low light test sets."""
        standard_samples: List[DatasetSampleMetadata] = []
        unseen_env_test: List[DatasetSampleMetadata] = []

        for s in samples:
            if s.environment in held_out_environments:
                s.split = SplitType.TEST_UNSEEN_ENVIRONMENT
                unseen_env_test.append(s)
            else:
                standard_samples.append(s)

        return standard_samples, unseen_env_test
