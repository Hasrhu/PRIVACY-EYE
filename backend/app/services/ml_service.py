"""
Privacy Eye — Core ML Service
Orchestrates image, video, and audio detection pipelines.

Architecture:
  - Real forensic signals (EXIF, frequency domain, metadata)
  - Real pretrained model inference (EfficientNet-based classifier)
  - Evidence fusion across multiple signals
  - Calibrated risk scoring
  - Explainable output

NOTE: Model weights require download via ml/scripts/download_models.py
      Until weights are downloaded, the service falls back to forensics-only mode
      clearly labeled as PROTOTYPE.
"""
import io
import hashlib
import asyncio
import time
from pathlib import Path
from typing import Any
import structlog

from app.core.config import settings

logger = structlog.get_logger(__name__)


class MLService:
    """
    Orchestrator for all media analysis pipelines.
    Loads image/video/audio sub-analyzers on warmup.
    """

    def __init__(self):
        self._ready = False
        self._model_info = {
            "name": "PrivacyEye-Ensemble-v1",
            "version": "1.0.0-mvp",
            "type": "ensemble",
            "inference_env": settings.ML_DEVICE,
            "components": {
                "image": "EfficientNet-B4 + Frequency Forensics",
                "video": "Frame-sampled EfficientNet + Temporal Consistency",
                "audio": "Mel-spectrogram CNN + Librosa Features",
            },
            "disclaimer": (
                "Results are probabilistic indicators only. "
                "Privacy Eye does not claim 100% accuracy. "
                "Always apply human judgment."
            ),
        }

    async def warmup(self):
        """Pre-load models into memory on startup."""
        try:
            from app.ml.image_analyzer import ImageAnalyzer
            from app.ml.video_analyzer import VideoAnalyzer
            from app.ml.audio_analyzer import AudioAnalyzer

            self._image = ImageAnalyzer()
            self._video = VideoAnalyzer()
            self._audio = AudioAnalyzer()
            self._ready = True
            logger.info("ML models warmed up", models=list(self._model_info["components"].keys()))
        except Exception as e:
            logger.warning("ML warmup failed — running in forensics-only mode", error=str(e))
            self._ready = False

    def get_model_info(self) -> dict:
        return self._model_info

    async def analyze(self, file_bytes: bytes, media_type: str, filename: str) -> dict:
        """
        Run the full analysis pipeline for a given media type.
        Returns a structured result dict.
        """
        t0 = time.monotonic()

        if media_type == "image":
            result = await self._analyze_image(file_bytes, filename)
        elif media_type == "video":
            result = await self._analyze_video(file_bytes, filename)
        elif media_type == "audio":
            result = await self._analyze_audio(file_bytes, filename)
        else:
            raise ValueError(f"Unknown media type: {media_type}")

        result["processing_ms"] = int((time.monotonic() - t0) * 1000)
        result["model_version"] = self._model_info["version"]
        return result

    async def _analyze_image(self, data: bytes, filename: str) -> dict:
        try:
            if self._ready:
                return await asyncio.get_event_loop().run_in_executor(
                    None, self._image.analyze, data, filename
                )
        except Exception as e:
            logger.warning("Image model failed, falling back to forensics", error=str(e))

        from app.ml.forensics import forensics_analyze_image
        return await asyncio.get_event_loop().run_in_executor(
            None, forensics_analyze_image, data, filename
        )

    async def _analyze_video(self, data: bytes, filename: str) -> dict:
        try:
            if self._ready:
                return await asyncio.get_event_loop().run_in_executor(
                    None, self._video.analyze, data, filename
                )
        except Exception as e:
            logger.warning("Video model failed, falling back to forensics", error=str(e))

        from app.ml.forensics import forensics_analyze_video
        return await asyncio.get_event_loop().run_in_executor(
            None, forensics_analyze_video, data, filename
        )

    async def _analyze_audio(self, data: bytes, filename: str) -> dict:
        try:
            if self._ready:
                return await asyncio.get_event_loop().run_in_executor(
                    None, self._audio.analyze, data, filename
                )
        except Exception as e:
            logger.warning("Audio model failed, falling back to forensics", error=str(e))

        from app.ml.forensics import forensics_analyze_audio
        return await asyncio.get_event_loop().run_in_executor(
            None, forensics_analyze_audio, data, filename
        )


ml_service = MLService()
