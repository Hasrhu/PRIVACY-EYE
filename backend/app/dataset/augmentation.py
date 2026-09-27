"""
Privacy Eye — Probabilistic Data Augmentation Engine
Applies stochastic, realistic degradations across Image, Video, and Sequence modalities
to prevent the detector from memorizing specific artifacts or confusing poor quality with fakeness.
"""

import random
from typing import List, Tuple, Optional
import numpy as np
import cv2


class ProbabilisticAugmentor:
    """Realistic, randomized data augmentation for face authenticity training."""

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    # ── Image Augmentations ──────────────────────────────────────────────────

    def augment_image(self, image: np.ndarray) -> np.ndarray:
        """Applies a randomized pipeline of visual corruptions to a single image frame."""
        img = image.copy()

        # 1. JPEG Compression (p=0.40)
        if random.random() < 0.40:
            quality = random.randint(20, 90)
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            _, enc = cv2.imencode(".jpg", img, encode_param)
            img = cv2.imdecode(enc, cv2.IMREAD_COLOR)

        # 2. Gaussian Blur / Motion Blur (p=0.30)
        if random.random() < 0.30:
            if random.random() < 0.5:
                # Gaussian Blur
                ksize = random.choice([3, 5, 7])
                sigma = random.uniform(0.5, 2.0)
                img = cv2.GaussianBlur(img, (ksize, ksize), sigma)
            else:
                # Directional Motion Blur
                ksize = random.choice([5, 9, 13])
                kernel_motion = np.zeros((ksize, ksize))
                kernel_motion[int((ksize - 1) / 2), :] = np.ones(ksize)
                kernel_motion = kernel_motion / ksize
                img = cv2.filter2D(img, -1, kernel_motion)

        # 3. Gaussian / Sensor Noise (p=0.30)
        if random.random() < 0.30:
            noise_sigma = random.uniform(5.0, 20.0)
            noise = np.random.normal(0, noise_sigma, img.shape).astype(np.float32)
            img = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)

        # 4. Brightness & Contrast (p=0.40)
        if random.random() < 0.40:
            alpha = random.uniform(0.7, 1.3)  # Contrast
            beta = random.uniform(-35, 35)    # Brightness
            img = np.clip(alpha * img.astype(np.float32) + beta, 0, 255).astype(np.uint8)

        # 5. Gamma Correction (p=0.35)
        if random.random() < 0.35:
            gamma = random.uniform(0.6, 1.5)
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            img = cv2.LUT(img, table)

        # 6. Downscale & Upscale (Resolution testing, p=0.35)
        if random.random() < 0.35:
            h, w = img.shape[:2]
            scale = random.uniform(0.35, 0.75)
            small = cv2.resize(img, (max(16, int(w * scale)), max(16, int(h * scale))), interpolation=cv2.INTER_LINEAR)
            img = cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)

        # 7. Subtle Perspective / Slight Rotation (p=0.25)
        if random.random() < 0.25:
            h, w = img.shape[:2]
            angle = random.uniform(-8.0, 8.0)
            center = (w // 2, h // 2)
            matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            img = cv2.warpAffine(img, matrix, (w, h), borderMode=cv2.BORDER_REFLECT)

        return img

    # ── Video Sequence Augmentations ──────────────────────────────────────────

    def augment_video_sequence(self, frames: List[np.ndarray]) -> List[np.ndarray]:
        """
        Applies temporal corruptions across a sequence of consecutive frames:
        - Frame dropping
        - Frame duplication (simulating stutter/low FPS)
        - Global lighting shift
        - Consistent or jittered blur
        """
        if not frames:
            return []

        seq = [f.copy() for f in frames]

        # 1. Frame Dropping / Skipping (p=0.30)
        if len(seq) > 6 and random.random() < 0.30:
            drop_step = random.choice([2, 3])
            seq = [seq[i] for i in range(0, len(seq), drop_step)]

        # 2. Variable FPS / Frame Duplication (p=0.25)
        if len(seq) > 4 and random.random() < 0.25:
            duplicated_seq = []
            for frame in seq:
                duplicated_seq.append(frame)
                if random.random() < 0.20:
                    duplicated_seq.append(frame.copy())  # Duplicated frame
            seq = duplicated_seq[:len(frames)]  # Maintain bounds

        # 3. Spatio-temporal noise & compression across frames
        quality = random.randint(25, 85)
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        augmented_seq = []
        for frame in seq:
            # Re-encode frame with variable bitrate simulation
            _, enc = cv2.imencode(".jpg", frame, encode_param)
            dec = cv2.imdecode(enc, cv2.IMREAD_COLOR)
            augmented_seq.append(dec)

        return augmented_seq

    # ── Audio Perturbations ──────────────────────────────────────────────────

    def augment_audio_features(self, audio_signal: np.ndarray, sample_rate: int = 16000) -> np.ndarray:
        """
        Synthetically augments audio signals:
        - Background Gaussian noise
        - Volume scaling
        - Sample rate downsampling / re-quantization
        """
        if audio_signal is None or len(audio_signal) == 0:
            return audio_signal

        sig = audio_signal.copy().astype(np.float32)

        # 1. Volume scaling
        scale = random.uniform(0.6, 1.4)
        sig = sig * scale

        # 2. Noise addition
        noise_amp = 0.005 * random.uniform(0.1, 1.0)
        noise = np.random.randn(len(sig)) * noise_amp
        sig = sig + noise

        # 3. Clip amplitude
        sig = np.clip(sig, -1.0, 1.0)
        return sig
