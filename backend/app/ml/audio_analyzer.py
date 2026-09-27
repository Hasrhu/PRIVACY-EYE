"""Audio Analyzer — Wav2Vec2-based voice clone detector."""
import numpy as np
from pathlib import Path
from app.core.config import settings

WEIGHTS_PATH = Path(settings.ML_MODELS_DIR) / "audio_wav2vec2_clone.onnx"


class AudioAnalyzer:
    def __init__(self):
        if not WEIGHTS_PATH.exists():
            raise FileNotFoundError(f"Audio model weights not found at {WEIGHTS_PATH}")
        import onnxruntime as ort
        self.session = ort.InferenceSession(str(WEIGHTS_PATH))
        self.input_name = self.session.get_inputs()[0].name

    def analyze(self, data: bytes, filename: str) -> dict:
        from app.ml.forensics import forensics_analyze_audio
        return forensics_analyze_audio(data, filename)
