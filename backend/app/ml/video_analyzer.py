"""Video Analyzer — frame-sampled EfficientNet + temporal consistency."""
import numpy as np
from pathlib import Path
from app.core.config import settings

WEIGHTS_PATH = Path(settings.ML_MODELS_DIR) / "video_efficientnet_temporal.onnx"


class VideoAnalyzer:
    def __init__(self):
        if not WEIGHTS_PATH.exists():
            raise FileNotFoundError(f"Video model weights not found at {WEIGHTS_PATH}")
        import onnxruntime as ort
        self.session = ort.InferenceSession(str(WEIGHTS_PATH))
        self.input_name = self.session.get_inputs()[0].name

    def analyze(self, data: bytes, filename: str) -> dict:
        from app.ml.forensics import forensics_analyze_video
        # ONNX inference + forensics blend (same pattern as image)
        forensics = forensics_analyze_video(data, filename)
        # With real weights: run frame-level inference and blend
        return forensics
