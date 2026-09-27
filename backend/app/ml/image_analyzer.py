"""
Image Analyzer — EfficientNet-B4 based deepfake classifier.
Requires model weights downloaded via ml/scripts/download_models.py

This is a REAL deep learning classifier. Without weights it raises
ImportError/FileNotFoundError and ml_service falls back to forensics.py.
"""
import io
import numpy as np
from pathlib import Path
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

WEIGHTS_PATH = Path(settings.ML_MODELS_DIR) / "image_efficientnet_b4.onnx"


class ImageAnalyzer:
    """
    EfficientNet-B4 deepfake image classifier.
    Trained on FaceForensics++ and DALL-E/Midjourney synthetic datasets.
    Inference via ONNX Runtime for cross-platform deployment.
    """

    def __init__(self):
        if not WEIGHTS_PATH.exists():
            raise FileNotFoundError(
                f"Image model weights not found at {WEIGHTS_PATH}. "
                "Run: python ml/scripts/download_models.py"
            )
        import onnxruntime as ort
        providers = ["CUDAExecutionProvider", "CPUExecutionProvider"] if settings.ML_DEVICE == "cuda" else ["CPUExecutionProvider"]
        self.session = ort.InferenceSession(str(WEIGHTS_PATH), providers=providers)
        self.input_name = self.session.get_inputs()[0].name
        logger.info("ImageAnalyzer loaded", path=str(WEIGHTS_PATH))

    def preprocess(self, data: bytes) -> np.ndarray:
        from PIL import Image
        img = Image.open(io.BytesIO(data)).convert("RGB").resize((380, 380))
        arr = np.array(img, dtype=np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        arr = (arr - mean) / std
        return arr.transpose(2, 0, 1)[np.newaxis].astype(np.float32)

    def analyze(self, data: bytes, filename: str) -> dict:
        from app.ml.forensics import forensics_analyze_image, _score_to_risk, _build_result

        inp = self.preprocess(data)
        outputs = self.session.run(None, {self.input_name: inp})
        logits = outputs[0][0]

        # Sigmoid for binary classification (fake=1, real=0)
        synthetic_prob = float(1 / (1 + np.exp(-logits[1] + logits[0])))
        confidence = min(0.92, abs(synthetic_prob - 0.5) * 2 + 0.60)

        # Augment with forensics signals
        forensics = forensics_analyze_image(data, filename)
        # Blend DL probability with forensics
        blended_prob = synthetic_prob * 0.7 + forensics["synthetic_probability"] * 0.3

        risk = _score_to_risk(blended_prob)
        signals = forensics["signals"]

        if synthetic_prob > 0.70:
            signals.insert(0, {
                "key": "dl_classifier_high",
                "label": "Deep learning classifier: high synthetic probability",
                "severity": "high",
                "score": round(synthetic_prob, 4),
                "description": "EfficientNet-B4 deepfake classifier assigns high synthetic probability to this image.",
            })

        return _build_result(
            risk_level=risk,
            synthetic_probability=round(blended_prob, 4),
            confidence=round(confidence, 4),
            signals=signals,
            explanation=f"EfficientNet-B4 classifier + forensics ensemble. DL score: {synthetic_prob:.2%}. Risk: {risk}.",
            provenance=forensics["provenance"],
            raw_scores={**forensics["raw_scores"], "dl_synthetic_prob": round(synthetic_prob, 4)},
        )
