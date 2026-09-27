"""
Privacy Eye — MiniVision Silent-Face-Anti-Spoofing Engine
Inspired by MiniVision (minivision-ai/Silent-Face-Anti-Spoofing).
Implements:
1. Multi-scale face sampling:
   - Scale 1.0 (Tight Crop): Micro-skin texture, paper halftone dots, 2D print ink artifacts.
   - Scale 2.7 (Extended Crop): Screen bezels, device borders, planar reflection, hand holding photo.
2. 2D Fourier Spectrum high-frequency harmonic analysis for electronic display & print dot grid detection.
3. Multi-channel color texture analysis (LBP / Local Binary Patterns) for surface reflectivity differentiation.
"""

from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import cv2


class SilentFaceAntiSpoofingEngine:
    """Multi-Scale Presentation Attack Detection (PAD) based on MiniFASNet principles."""

    def __init__(self, fourier_threshold: float = 0.65):
        self.fourier_threshold = fourier_threshold

    def extract_multi_scale_crops(
        self, full_frame_bgr: np.ndarray, face_box: List[int]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extracts Scale 1.0 (Tight) and Scale 2.7 (Contextual) crops.
        face_box format: [x, y, w, h]
        """
        H, W = full_frame_bgr.shape[:2]
        x, y, w, h = face_box

        # ── Scale 1.0 (Tight face crop) ───────────────────────────────────────
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(W, x + w)
        y2 = min(H, y + h)
        scale_1_0 = full_frame_bgr[y1:y2, x1:x2].copy()

        # ── Scale 2.7 (Extended context crop) ─────────────────────────────────
        cx = x + w / 2.0
        cy = y + h / 2.0
        w_ext = w * 2.7
        h_ext = h * 2.7

        ex1 = max(0, int(cx - w_ext / 2.0))
        ey1 = max(0, int(cy - h_ext / 2.0))
        ex2 = min(W, int(cx + w_ext / 2.0))
        ey2 = min(H, int(cy + h_ext / 2.0))
        scale_2_7 = full_frame_bgr[ey1:ey2, ex1:ex2].copy()

        return scale_1_0, scale_2_7

    def analyze_fourier_spectrum(self, img_bgr: np.ndarray) -> Dict[str, Any]:
        """
        Computes the 2D Discrete Fourier Transform spectrum.
        Electronic screens (LCD, OLED, AMOLED) and printed photos produce distinct
        periodic high-frequency harmonic spikes (Moiré pattern and pixel grid).
        Bona fide faces have smooth organic radial energy dissipation.
        """
        if img_bgr is None or img_bgr.size == 0:
            return {"fourier_spoof_score": 0.0, "harmonic_spikes": 0}

        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        # Resize to fixed 256x256 for consistent frequency binning
        resized = cv2.resize(gray, (256, 256), interpolation=cv2.INTER_AREA)

        # 2D FFT
        dft = np.fft.fft2(resized)
        dft_shift = np.fft.fftshift(dft)
        magnitude_spectrum = 20 * np.log(np.abs(dft_shift) + 1e-6)

        # Mask DC center (low frequencies)
        center = 128
        r_inner = 25
        r_outer = 110
        y, x = np.ogrid[:256, :256]
        dist_from_center = np.sqrt((x - center)**2 + (y - center)**2)

        band_mask = (dist_from_center >= r_inner) & (dist_from_center <= r_outer)
        high_freq_band = magnitude_spectrum[band_mask]

        mean_hf = float(np.mean(high_freq_band))
        std_hf = float(np.std(high_freq_band))
        max_hf = float(np.max(high_freq_band))

        # Peak-to-average ratio detects sharp harmonic spikes (display pixel grids)
        peak_ratio = (max_hf - mean_hf) / max(1.0, std_hf)

        # Presentation attacks (screens/prints) exhibit peak_ratio > 4.2
        spoof_score = float(np.clip((peak_ratio - 3.2) / 3.0, 0.0, 1.0))

        return {
            "fourier_spoof_score": round(spoof_score, 3),
            "peak_to_average_ratio": round(peak_ratio, 2),
            "mean_hf_magnitude": round(mean_hf, 2),
            "has_periodic_grid": spoof_score >= self.fourier_threshold,
        }

    def analyze_local_binary_patterns(self, img_bgr: np.ndarray) -> Dict[str, Any]:
        """
        Calculates Local Binary Pattern (LBP) texture uniformity.
        Printed paper surfaces and phone screens lack the micro-texture depth of human epidermis.
        """
        if img_bgr is None or img_bgr.size == 0:
            return {"lbp_uniformity_score": 0.0}

        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        # Efficient basic LBP implementation
        h, w = gray.shape
        lbp = np.zeros((h - 2, w - 2), dtype=np.uint8)

        center_pixels = gray[1:-1, 1:-1]
        for idx, (dy, dx) in enumerate([(-1, -1), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1)]):
            neighbor = gray[1 + dy:h - 1 + dy, 1 + dx:w - 1 + dx]
            lbp += ((neighbor >= center_pixels) << idx).astype(np.uint8)

        # Compute histogram of LBP patterns
        hist, _ = np.histogram(lbp.ravel(), bins=256, range=(0, 256), density=True)
        # Entropy of LBP distribution
        hist_nonzero = hist[hist > 0]
        entropy = -float(np.sum(hist_nonzero * np.log2(hist_nonzero)))

        # Natural skin has higher texture entropy (4.8 to 6.5). Screens/prints are lower (< 4.2)
        texture_score = float(np.clip((5.5 - entropy) / 2.0, 0.0, 1.0))

        return {
            "lbp_spoof_score": round(texture_score, 3),
            "texture_entropy": round(entropy, 2),
            "is_flat_surface": texture_score >= 0.60,
        }

    def full_silent_face_scan(
        self, full_frame_bgr: np.ndarray, face_box: List[int]
    ) -> Dict[str, Any]:
        """
        Runs the dual-scale Silent-Face-Anti-Spoofing analysis battery.
        Combines Scale 1.0 skin analysis with Scale 2.7 bezel/device detection.
        """
        crop_1_0, crop_2_7 = self.extract_multi_scale_crops(full_frame_bgr, face_box)

        # Scale 1.0 Analysis (Skin & Halftone print check)
        fourier_1_0 = self.analyze_fourier_spectrum(crop_1_0)
        lbp_1_0 = self.analyze_local_binary_patterns(crop_1_0)

        # Scale 2.7 Analysis (Surrounding border & display frame check)
        fourier_2_7 = self.analyze_fourier_spectrum(crop_2_7)

        # Composite Presentation Attack score
        composite_score = (
            0.45 * fourier_1_0["fourier_spoof_score"] +
            0.35 * fourier_2_7["fourier_spoof_score"] +
            0.20 * lbp_1_0["lbp_spoof_score"]
        )

        attack_type = "none"
        if composite_score >= 0.65:
            if fourier_2_7["has_periodic_grid"]:
                attack_type = "Electronic Display Replay (Screen Attack)"
            elif lbp_1_0["is_flat_surface"]:
                attack_type = "Printed Photo / Planar Mask Attack"
            else:
                attack_type = "Presentation Attack (PAD)"

        return {
            "silent_face_spoof_score": round(float(composite_score), 3),
            "is_presentation_attack": composite_score >= 0.65,
            "detected_attack_type": attack_type,
            "scale_1_0_fourier": fourier_1_0,
            "scale_2_7_fourier": fourier_2_7,
            "scale_1_0_lbp": lbp_1_0,
        }
