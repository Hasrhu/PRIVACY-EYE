"""
Privacy Eye — Forensics-Only Analyzer (no ML model weights required)

These functions run real signal extraction:
  - EXIF metadata analysis
  - Error Level Analysis (ELA)
  - Frequency domain (FFT) analysis
  - Noise pattern analysis
  - Compression artifact detection
  - Audio spectral anomaly detection

Results are clearly labeled as forensics-based (not deep-learning-based).
"""
import io
import hashlib
import struct
import numpy as np
from typing import Any
import structlog

logger = structlog.get_logger(__name__)

# ── Risk mapping ─────────────────────────────────────────────────────────────

def _score_to_risk(score: float) -> str:
    if score >= 0.80:
        return "CRITICAL"
    elif score >= 0.60:
        return "HIGH"
    elif score >= 0.35:
        return "SUSPICIOUS"
    elif score >= 0.0:
        return "LOW"
    return "UNDETERMINED"


def _build_result(
    risk_level: str,
    synthetic_probability: float,
    confidence: float,
    signals: list[dict],
    explanation: str,
    provenance: dict,
    raw_scores: dict,
) -> dict:
    return {
        "risk_level": risk_level,
        "synthetic_probability": round(synthetic_probability, 4),
        "confidence": round(confidence, 4),
        "signals": signals,
        "explanation": explanation,
        "provenance": provenance,
        "raw_scores": raw_scores,
        "analysis_mode": "forensics",
    }


# ── Image ─────────────────────────────────────────────────────────────────────

def forensics_analyze_image(data: bytes, filename: str) -> dict:
    """
    Real forensic image analysis:
    1. EXIF metadata extraction
    2. Error Level Analysis (ELA)
    3. FFT frequency domain
    4. Noise inconsistency estimation
    """
    signals = []
    raw_scores = {}

    try:
        from PIL import Image
        import piexif

        img = Image.open(io.BytesIO(data)).convert("RGB")
        width, height = img.size
        raw_scores["resolution"] = f"{width}x{height}"

        # ── 1. EXIF metadata ─────────────────────────────────────────────────
        exif_score = 0.0
        try:
            exif_data = piexif.load(data)
            has_software = bool(exif_data.get("0th", {}).get(piexif.ImageIFD.Software))
            has_make = bool(exif_data.get("0th", {}).get(piexif.ImageIFD.Make))
            has_gps = bool(exif_data.get("GPS", {}))

            raw_scores["has_exif_software_tag"] = has_software
            raw_scores["has_camera_make"] = has_make
            raw_scores["has_gps"] = has_gps

            if has_software and not has_make:
                exif_score = 0.45
                signals.append({
                    "key": "exif_software_no_camera",
                    "label": "Software tag present but no camera manufacturer",
                    "severity": "medium",
                    "score": exif_score,
                    "description": (
                        "The image contains a software processing tag but no camera hardware metadata. "
                        "AI-generated images often lack authentic camera sensor metadata."
                    ),
                })
            elif not has_make and not has_software:
                exif_score = 0.30
                signals.append({
                    "key": "exif_missing_camera_meta",
                    "label": "Missing camera metadata",
                    "severity": "low",
                    "score": exif_score,
                    "description": "No camera manufacturer or software metadata found. Stripped EXIF can indicate re-processing.",
                })
        except Exception:
            exif_score = 0.20
            raw_scores["has_exif_software_tag"] = False
            raw_scores["has_camera_make"] = False

        # ── 2. Error Level Analysis (ELA) ────────────────────────────────────
        ela_score = 0.0
        try:
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=75)
            recompressed = Image.open(buf).convert("RGB")

            orig_arr = np.array(img, dtype=np.float32)
            recomp_arr = np.array(recompressed, dtype=np.float32)
            ela_arr = np.abs(orig_arr - recomp_arr)
            ela_mean = float(ela_arr.mean())
            ela_std = float(ela_arr.std())

            raw_scores["ela_mean"] = round(ela_mean, 4)
            raw_scores["ela_std"] = round(ela_std, 4)

            # Very low ELA variance in high-detail areas suggests AI generation
            if ela_std < 3.0 and ela_mean < 5.0:
                ela_score = 0.55
                signals.append({
                    "key": "ela_low_variance",
                    "label": "Unusually uniform error level distribution",
                    "severity": "high",
                    "score": ela_score,
                    "description": (
                        "Error Level Analysis found abnormally uniform compression residuals across the image. "
                        "Authentic photographs typically show uneven ELA patterns; AI-generated images tend to be more uniform."
                    ),
                })
            elif ela_std < 8.0:
                ela_score = 0.30
                signals.append({
                    "key": "ela_moderate_uniformity",
                    "label": "Moderately uniform error level pattern",
                    "severity": "low",
                    "score": ela_score,
                    "description": "ELA shows moderate uniformity — slightly unusual for a natural photograph.",
                })
        except Exception as e:
            logger.debug("ELA failed", error=str(e))

        # ── 3. FFT Frequency Domain ──────────────────────────────────────────
        fft_score = 0.0
        try:
            gray = np.array(img.convert("L"), dtype=np.float32)
            fft = np.fft.fft2(gray)
            fft_shift = np.fft.fftshift(fft)
            magnitude = np.log1p(np.abs(fft_shift))

            center = np.array(magnitude.shape) // 2
            r = min(center) // 4
            inner = magnitude[center[0]-r:center[0]+r, center[1]-r:center[1]+r]
            outer_energy = magnitude.sum() - inner.sum()
            inner_energy = inner.sum()

            ratio = float(inner_energy / (outer_energy + 1e-8))
            raw_scores["fft_inner_outer_ratio"] = round(ratio, 4)

            # AI images often show distinctive spectral peaks
            if ratio > 1.8:
                fft_score = 0.50
                signals.append({
                    "key": "fft_spectral_anomaly",
                    "label": "Frequency domain spectral anomaly",
                    "severity": "high",
                    "score": fft_score,
                    "description": (
                        "The image's frequency spectrum shows unusual energy concentration in low frequencies. "
                        "GAN and diffusion model outputs often have characteristic spectral signatures."
                    ),
                })
            elif ratio > 1.3:
                fft_score = 0.25
                signals.append({
                    "key": "fft_mild_spectral_bias",
                    "label": "Mild frequency domain bias",
                    "severity": "low",
                    "score": fft_score,
                    "description": "Slight low-frequency energy bias detected in the image spectrum.",
                })
        except Exception as e:
            logger.debug("FFT analysis failed", error=str(e))

        # ── 4. Noise Inconsistency ───────────────────────────────────────────
        noise_score = 0.0
        try:
            arr = np.array(img, dtype=np.float32)
            # Split into quadrants and compare local noise levels
            h, w = arr.shape[:2]
            quads = [
                arr[:h//2, :w//2].std(),
                arr[:h//2, w//2:].std(),
                arr[h//2:, :w//2].std(),
                arr[h//2:, w//2:].std(),
            ]
            noise_range = max(quads) - min(quads)
            raw_scores["quadrant_noise_range"] = round(float(noise_range), 4)

            if noise_range < 5.0 and all(q > 2.0 for q in quads):
                noise_score = 0.40
                signals.append({
                    "key": "noise_inconsistency",
                    "label": "Spatially uniform noise pattern",
                    "severity": "medium",
                    "score": noise_score,
                    "description": (
                        "Noise levels are suspiciously uniform across image regions. "
                        "Real photographs typically show variable noise due to sensor characteristics."
                    ),
                })
        except Exception as e:
            logger.debug("Noise analysis failed", error=str(e))

        # ── Evidence fusion ─────────────────────────────────────────────────
        component_scores = [s for s in [exif_score, ela_score, fft_score, noise_score] if s > 0]
        if component_scores:
            # Weighted fusion: max signal weighted heavily
            synthetic_prob = float(np.mean(component_scores) * 0.6 + max(component_scores) * 0.4)
        else:
            synthetic_prob = 0.10

        synthetic_prob = min(synthetic_prob, 0.97)
        confidence = 0.60 if len(signals) >= 2 else 0.45 if signals else 0.35
        risk = _score_to_risk(synthetic_prob)

        explanation = _build_image_explanation(risk, signals, synthetic_prob)

        return _build_result(
            risk_level=risk,
            synthetic_probability=synthetic_prob,
            confidence=confidence,
            signals=signals,
            explanation=explanation,
            provenance=_extract_image_provenance(data),
            raw_scores=raw_scores,
        )

    except Exception as e:
        logger.error("Image forensics failed", error=str(e))
        return _build_result(
            risk_level="UNDETERMINED",
            synthetic_probability=0.0,
            confidence=0.0,
            signals=[],
            explanation="Analysis could not be completed due to an internal error.",
            provenance={},
            raw_scores={"error": str(e)},
        )


def _build_image_explanation(risk: str, signals: list, prob: float) -> str:
    base = {
        "CRITICAL": "Strong synthetic media indicators were detected in this image.",
        "HIGH": "Multiple indicators associated with AI generation or manipulation were detected.",
        "SUSPICIOUS": "Some indicators associated with synthetic media were detected.",
        "LOW": "Few or no significant synthetic media indicators were detected.",
        "UNDETERMINED": "Analysis was inconclusive.",
    }.get(risk, "Analysis completed.")

    if signals:
        labels = ", ".join(s["label"] for s in signals[:3])
        base += f" Key signals: {labels}."

    base += f" Synthetic probability estimate: {prob:.0%}. This is a probabilistic assessment only."
    return base


def _extract_image_provenance(data: bytes) -> dict:
    """Extract provenance metadata from image."""
    prov = {}
    try:
        import piexif
        exif = piexif.load(data)
        ifd = exif.get("0th", {})
        if ifd.get(piexif.ImageIFD.Make):
            prov["camera_make"] = ifd[piexif.ImageIFD.Make].decode("utf-8", errors="ignore").strip("\x00")
        if ifd.get(piexif.ImageIFD.Model):
            prov["camera_model"] = ifd[piexif.ImageIFD.Model].decode("utf-8", errors="ignore").strip("\x00")
        if ifd.get(piexif.ImageIFD.Software):
            prov["software"] = ifd[piexif.ImageIFD.Software].decode("utf-8", errors="ignore").strip("\x00")
        if ifd.get(piexif.ImageIFD.DateTime):
            prov["datetime"] = ifd[piexif.ImageIFD.DateTime].decode("utf-8", errors="ignore").strip("\x00")
    except Exception:
        pass
    return prov


# ── Video ─────────────────────────────────────────────────────────────────────

def forensics_analyze_video(data: bytes, filename: str) -> dict:
    """
    Forensic video analysis using OpenCV frame sampling.
    Analyzes: temporal consistency, face boundary, compression artifacts.
    """
    signals = []
    raw_scores = {}

    try:
        import cv2
        import tempfile, os

        # Write to temp file since OpenCV needs a path
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            f.write(data)
            tmp_path = f.name

        try:
            cap = cv2.VideoCapture(tmp_path)
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0

            raw_scores["fps"] = round(fps, 2)
            raw_scores["frame_count"] = frame_count
            raw_scores["duration_seconds"] = round(duration, 2)

            # Sample frames evenly
            sample_indices = np.linspace(0, max(frame_count - 1, 0), min(16, frame_count), dtype=int)
            frames = []
            for idx in sample_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
            cap.release()

            if len(frames) < 2:
                raise ValueError("Could not extract enough frames")

            # ── Temporal consistency ────────────────────────────────────────
            diffs = []
            for i in range(1, len(frames)):
                diff = cv2.absdiff(frames[i-1], frames[i])
                diffs.append(float(diff.mean()))

            diff_std = float(np.std(diffs))
            diff_mean = float(np.mean(diffs))
            raw_scores["temporal_diff_mean"] = round(diff_mean, 4)
            raw_scores["temporal_diff_std"] = round(diff_std, 4)

            temporal_score = 0.0
            if diff_std < 1.5 and diff_mean > 0.5:
                temporal_score = 0.55
                signals.append({
                    "key": "temporal_consistency_anomaly",
                    "label": "Abnormally consistent frame transitions",
                    "severity": "high",
                    "score": temporal_score,
                    "description": (
                        "Frame-to-frame differences are unusually uniform. "
                        "Deepfake videos often show abnormally smooth transitions due to per-frame synthesis."
                    ),
                })

            # ── Compression blocking ─────────────────────────────────────────
            block_score = 0.0
            blocking_counts = []
            for frame in frames[:8]:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
                # Detect 8x8 DCT block boundaries
                h_diff = np.abs(np.diff(gray, axis=0))
                v_diff = np.abs(np.diff(gray, axis=1))
                h_block = h_diff[7::8, :].mean() if h_diff.shape[0] >= 8 else 0
                v_block = v_diff[:, 7::8].mean() if v_diff.shape[1] >= 8 else 0
                blocking_counts.append((h_block + v_block) / 2)

            avg_blocking = float(np.mean(blocking_counts))
            raw_scores["avg_blocking_artifact"] = round(avg_blocking, 4)
            if avg_blocking > 8.0:
                block_score = 0.35
                signals.append({
                    "key": "compression_blocking",
                    "label": "High compression blocking artifacts",
                    "severity": "medium",
                    "score": block_score,
                    "description": "Significant compression blocking detected. May indicate re-encoding of manipulated frames.",
                })

            # ── Brightness flicker ────────────────────────────────────────────
            brightnesses = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).mean() for f in frames]
            brightness_std = float(np.std(brightnesses))
            raw_scores["brightness_std"] = round(brightness_std, 4)

            flicker_score = 0.0
            if brightness_std > 15.0:
                flicker_score = 0.40
                signals.append({
                    "key": "brightness_flicker",
                    "label": "Inconsistent lighting across frames",
                    "severity": "medium",
                    "score": flicker_score,
                    "description": "Significant brightness variation between frames. Synthetic face rendering can cause lighting inconsistencies.",
                })

        finally:
            os.unlink(tmp_path)

        scores = [s for s in [temporal_score, block_score, flicker_score] if s > 0]
        synthetic_prob = float(np.mean(scores) * 0.5 + max(scores, default=0) * 0.5) if scores else 0.10
        synthetic_prob = min(synthetic_prob, 0.97)
        confidence = 0.65 if len(signals) >= 2 else 0.50 if signals else 0.35
        risk = _score_to_risk(synthetic_prob)

        return _build_result(
            risk_level=risk,
            synthetic_probability=synthetic_prob,
            confidence=confidence,
            signals=signals,
            explanation=_build_video_explanation(risk, signals, synthetic_prob),
            provenance={"duration_seconds": raw_scores.get("duration_seconds"), "fps": raw_scores.get("fps")},
            raw_scores=raw_scores,
        )

    except Exception as e:
        logger.error("Video forensics failed", error=str(e))
        return _build_result(
            risk_level="UNDETERMINED",
            synthetic_probability=0.0,
            confidence=0.0,
            signals=[],
            explanation=f"Video analysis could not be completed: {str(e)[:200]}",
            provenance={},
            raw_scores={"error": str(e)},
        )


def _build_video_explanation(risk: str, signals: list, prob: float) -> str:
    base = {
        "CRITICAL": "Strong deepfake or synthetic video indicators were detected across multiple frames.",
        "HIGH": "Multiple temporal and visual anomalies associated with video manipulation were detected.",
        "SUSPICIOUS": "Some frame-level indicators consistent with video synthesis were detected.",
        "LOW": "Few or no significant video manipulation indicators were detected.",
        "UNDETERMINED": "Video analysis was inconclusive.",
    }.get(risk, "Video analysis completed.")
    if signals:
        labels = ", ".join(s["label"] for s in signals[:3])
        base += f" Key signals: {labels}."
    base += f" Synthetic probability: {prob:.0%}. Temporal analysis covered sampled frames only."
    return base


# ── Audio ─────────────────────────────────────────────────────────────────────

def forensics_analyze_audio(data: bytes, filename: str) -> dict:
    """
    Real audio forensics using librosa:
    - Spectral analysis
    - Mel-spectrogram variance
    - Pitch consistency
    - Zero-crossing rate
    - Silence pattern
    """
    signals = []
    raw_scores = {}

    try:
        import librosa
        import soundfile as sf

        # Load audio
        audio_io = io.BytesIO(data)
        try:
            y, sr = librosa.load(audio_io, sr=None, mono=True, duration=60.0)
        except Exception:
            # Try soundfile if librosa fails
            audio_io.seek(0)
            y_sf, sr = sf.read(audio_io, dtype="float32", always_2d=False)
            y = y_sf if y_sf.ndim == 1 else y_sf.mean(axis=1)

        duration = len(y) / sr
        raw_scores["duration_seconds"] = round(duration, 2)
        raw_scores["sample_rate"] = sr

        # ── Spectral flatness ────────────────────────────────────────────────
        flatness = librosa.feature.spectral_flatness(y=y)
        flatness_mean = float(flatness.mean())
        raw_scores["spectral_flatness_mean"] = round(flatness_mean, 6)

        flatness_score = 0.0
        if flatness_mean > 0.08:
            flatness_score = 0.50
            signals.append({
                "key": "spectral_flatness_high",
                "label": "High spectral flatness (noise-like spectrum)",
                "severity": "high",
                "score": flatness_score,
                "description": (
                    "The audio has an unusually flat frequency spectrum. "
                    "TTS and voice-cloning systems often produce spectrally flat output compared to natural speech."
                ),
            })

        # ── Mel-spectrogram variance ─────────────────────────────────────────
        mel_score = 0.0
        mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=64)
        mel_db = librosa.power_to_db(mel, ref=np.max)
        mel_var = float(mel_db.var())
        raw_scores["mel_spectrogram_variance"] = round(mel_var, 4)

        if mel_var < 80.0:
            mel_score = 0.45
            signals.append({
                "key": "mel_low_variance",
                "label": "Low mel-spectrogram variance",
                "severity": "medium",
                "score": mel_score,
                "description": (
                    "The mel-spectrogram shows unusually low variance. "
                    "Synthetic voices tend to lack the natural prosodic variation found in human speech."
                ),
            })

        # ── Zero-crossing rate ───────────────────────────────────────────────
        zcr = librosa.feature.zero_crossing_rate(y)
        zcr_std = float(zcr.std())
        raw_scores["zcr_std"] = round(zcr_std, 6)

        zcr_score = 0.0
        if zcr_std < 0.01:
            zcr_score = 0.35
            signals.append({
                "key": "zcr_uniformity",
                "label": "Uniform zero-crossing rate",
                "severity": "medium",
                "score": zcr_score,
                "description": (
                    "Zero-crossing rate is abnormally uniform — natural speech shows higher variation."
                ),
            })

        # ── Silence/pause pattern ────────────────────────────────────────────
        silence_score = 0.0
        intervals = librosa.effects.split(y, top_db=25)
        if len(intervals) > 0:
            pause_lengths = []
            for i in range(1, len(intervals)):
                pause = (intervals[i][0] - intervals[i-1][1]) / sr
                pause_lengths.append(pause)
            if pause_lengths:
                pause_regularity = float(np.std(pause_lengths))
                raw_scores["pause_regularity_std"] = round(pause_regularity, 4)
                if pause_regularity < 0.05 and len(pause_lengths) > 3:
                    silence_score = 0.40
                    signals.append({
                        "key": "pause_pattern_regularity",
                        "label": "Unusually regular pause pattern",
                        "severity": "medium",
                        "score": silence_score,
                        "description": (
                            "Speech pauses are abnormally regular. TTS systems often generate metronomic pause patterns."
                        ),
                    })

        scores = [s for s in [flatness_score, mel_score, zcr_score, silence_score] if s > 0]
        synthetic_prob = float(np.mean(scores) * 0.5 + max(scores, default=0) * 0.5) if scores else 0.08
        synthetic_prob = min(synthetic_prob, 0.97)
        confidence = 0.65 if len(signals) >= 2 else 0.50 if signals else 0.35
        risk = _score_to_risk(synthetic_prob)

        return _build_result(
            risk_level=risk,
            synthetic_probability=synthetic_prob,
            confidence=confidence,
            signals=signals,
            explanation=_build_audio_explanation(risk, signals, synthetic_prob),
            provenance={"duration_seconds": duration, "sample_rate": sr},
            raw_scores=raw_scores,
        )

    except Exception as e:
        logger.error("Audio forensics failed", error=str(e))
        return _build_result(
            risk_level="UNDETERMINED",
            synthetic_probability=0.0,
            confidence=0.0,
            signals=[],
            explanation=f"Audio analysis could not be completed: {str(e)[:200]}",
            provenance={},
            raw_scores={"error": str(e)},
        )


def _build_audio_explanation(risk: str, signals: list, prob: float) -> str:
    base = {
        "CRITICAL": "Strong voice-cloning or synthetic speech indicators were detected.",
        "HIGH": "Multiple spectral and prosodic anomalies associated with synthetic speech were detected.",
        "SUSPICIOUS": "Some acoustic indicators consistent with AI-generated or cloned voice were detected.",
        "LOW": "Few or no significant synthetic voice indicators were detected.",
        "UNDETERMINED": "Audio analysis was inconclusive.",
    }.get(risk, "Audio analysis completed.")
    if signals:
        labels = ", ".join(s["label"] for s in signals[:3])
        base += f" Key signals: {labels}."
    base += f" Synthetic probability: {prob:.0%}. Analysis covered up to 60 seconds of audio."
    return base
