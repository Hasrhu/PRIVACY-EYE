"""
Privacy Eye — Forensic Benchmark Analyzers
Integrations inspired by landmark forensic research:
- FaceForensics++ (Boundary blending, multi-compression artifacts, manipulation classes)
- Celeb-DF v2 (Blinking dynamics, landmark stability, synthesis boundary masking)
- MiniVision Silent-Face-Anti-Spoofing (Multi-scale 1.0/2.7 Fourier spectrum, LBP presentation attack detection)
- NVIDIA FFHQ (High-resolution texture baseline, compliance guardrails)
"""

from app.ml.benchmarks.faceforensics import FaceForensicsAnalyzer
from app.ml.benchmarks.celeb_df import CelebDFAnalyzer
from app.ml.benchmarks.silent_face import SilentFaceAntiSpoofingEngine
from app.ml.benchmarks.ffhq_policy import FFHQPolicyProcessor

__all__ = [
    "FaceForensicsAnalyzer",
    "CelebDFAnalyzer",
    "SilentFaceAntiSpoofingEngine",
    "FFHQPolicyProcessor",
]
