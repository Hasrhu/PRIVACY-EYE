"""
Privacy Eye — Dataset Taxonomy & Metadata Specification
Defines the five major dataset categories, provenance metadata, labels, and state spaces.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import enum
from typing import Optional, Dict, Any, List


class DatasetCategory(str, enum.Enum):
    """The 5 foundational dataset categories for Privacy Eye."""
    CATEGORY_A_GENUINE = "CATEGORY_A_GENUINE"              # Authorized, consented bona fide live human recordings
    CATEGORY_B_SYNTHETIC = "CATEGORY_B_SYNTHETIC"          # Pure AI-generated synthetic faces (GAN & Diffusion)
    CATEGORY_C_DEEPFAKE = "CATEGORY_C_DEEPFAKE"            # Face-swap / Facial manipulation (DeepFaceLab, Face2Face, etc.)
    CATEGORY_D_REPLAY = "CATEGORY_D_REPLAY"                # Presentation attacks (Photo, screen replay, 3D masks)
    CATEGORY_E_HARD_NEGATIVE = "CATEGORY_E_HARD_NEGATIVE"  # Real humans under extreme degradation / screen hard negatives


class ResultState(str, enum.Enum):
    """
    Final decision state space.
    Strictly avoids naive binary REAL/FAKE output.
    """
    LIKELY_LIVE_HUMAN = "LIKELY LIVE HUMAN"
    LIKELY_SYNTHETIC = "LIKELY SYNTHETIC"
    POSSIBLE_FACE_SWAP = "POSSIBLE FACE SWAP"
    POSSIBLE_REPLAY = "POSSIBLE REPLAY"
    POSSIBLE_PRESENTATION_ATTACK = "POSSIBLE PRESENTATION ATTACK"
    SUSPICIOUS = "SUSPICIOUS"
    UNABLE_TO_DETERMINE = "UNABLE TO DETERMINE"


class ManipulationType(str, enum.Enum):
    NONE = "none"
    DEEPFAKES = "deepfakes"
    FACE2FACE = "face2face"
    FACESWAP = "faceswap"
    NEURAL_TEXTURES = "neural_textures"
    FACESHIFTER = "faceshifter"
    GAN_SYNTHETIC = "gan_synthetic"
    DIFFUSION_SYNTHETIC = "diffusion_synthetic"
    PRINT_ATTACK = "print_attack"
    SCREEN_REPLAY = "screen_replay"
    MASK_ATTACK = "mask_attack"
    SCREEN_RECORDING = "screen_recording"


class GeneratorFamily(str, enum.Enum):
    NONE = "none"
    STYLEGAN2 = "stylegan2"
    STYLEGAN3 = "stylegan3"
    PROGAN = "progan"
    STABLE_DIFFUSION_15 = "stable_diffusion_15"
    SDXL = "sdxl"
    MIDJOURNEY_V5 = "midjourney_v5"
    MIDJOURNEY_V6 = "midjourney_v6"
    FLUX_1 = "flux_1"
    DEEPFACELAB = "deepfacelab"
    SIMSWAP = "simswap"


class EnvironmentType(str, enum.Enum):
    BEDROOM = "bedroom"
    OFFICE = "office"
    CLASSROOM = "classroom"
    OUTDOOR_SUNNY = "outdoor_sunny"
    OUTDOOR_OVERCAST = "outdoor_overcast"
    INDOOR_BRIGHT = "indoor_bright"
    INDOOR_DIM = "indoor_dim"
    BACKLIT = "backlit"
    SIDE_LIT = "side_lit"
    MIXED_LIGHTING = "mixed_lighting"
    EXTREME_LOW_LIGHT = "extreme_low_light"


class DeviceClass(str, enum.Enum):
    LAPTOP_WEBCAM_720P = "laptop_webcam_720p"
    LAPTOP_WEBCAM_1080P = "laptop_webcam_1080p"
    LOW_COST_USB_WEBCAM = "low_cost_usb_webcam"
    HIGH_QUALITY_WEBCAM = "high_quality_webcam"
    ANDROID_ENTRY = "android_entry"
    ANDROID_FLAGSHIP = "android_flagship"
    IPHONE_STANDARD = "iphone_standard"
    IPHONE_PRO = "iphone_pro"
    TABLET = "tablet"


class ResolutionPreset(str, enum.Enum):
    RES_360P = "360p"
    RES_480P = "480p"
    RES_720P = "720p"
    RES_1080P = "1080p"


class SplitType(str, enum.Enum):
    TRAIN = "train"
    VAL = "val"
    TEST_SEEN = "test_seen"
    TEST_UNSEEN_SUBJECT = "test_unseen_subject"
    TEST_UNSEEN_GENERATOR = "test_unseen_generator"
    TEST_UNSEEN_DEVICE = "test_unseen_device"
    TEST_UNSEEN_ENVIRONMENT = "test_unseen_environment"
    ADVERSARIAL_TEST = "adversarial_test"


@dataclass
class DatasetSampleMetadata:
    """Complete provenance and configuration metadata for each sample."""
    sample_id: str
    category: DatasetCategory
    source_dataset: str
    license_terms: str
    subject_id: Optional[str] = None
    video_id: Optional[str] = None
    generator: GeneratorFamily = GeneratorFamily.NONE
    manipulation: ManipulationType = ManipulationType.NONE
    device: DeviceClass = DeviceClass.LAPTOP_WEBCAM_720P
    environment: EnvironmentType = EnvironmentType.INDOOR_BRIGHT
    resolution: ResolutionPreset = ResolutionPreset.RES_720P
    fps: int = 30
    true_label: str = "real"  # "real", "fake", "replay", "hard_negative"
    split: SplitType = SplitType.TRAIN
    consent_status: bool = True
    collection_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    attributes: Dict[str, Any] = field(default_factory=dict)
    # Attributes explicitly store visual physical props only (e.g. glasses=True, beard=True)
    # NEVER demographic profiling (no race, gender, political, or emotional inferences).
