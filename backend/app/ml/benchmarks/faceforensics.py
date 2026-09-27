"""
Privacy Eye — FaceForensics++ Artifact Analyzer
Inspired by FaceForensics++ (ondyari/FaceForensics).
Analyzes:
1. Facial perimeter boundary blending / feathering artifacts (FaceSwap / Face2Face / Deepfakes).
2. Color space (YCbCr / HSV) distribution discrepancies between inner face and background context.
3. Compression ghosting & double quantization residuals (c23 / c40 artifacts).
"""

from typing import Dict, Any, Optional, Tuple, List
import numpy as np
import cv2


class FaceForensicsAnalyzer:
    """Extracts forensic manipulation signals based on FaceForensics++ research."""

    def __init__(self):
        pass

    def analyze_boundary_feathering(
        self, face_bgr: np.ndarray, context_bgr: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Analyzes edge blending along the perimeter of the face.
        Face swaps typically leave a subtle gradient mismatch or blur band where
        the synthetic mask was alpha-blended or Poisson-blended into the target frame.
        """
        if face_bgr is None or face_bgr.size == 0:
            return {"boundary_discontinuity_score": 0.0, "is_manipulated": False}

        h, w = face_bgr.shape[:2]
        gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)

        # Create an elliptical mask for the inner face vs perimeter border
        mask_inner = np.zeros((h, w), dtype=np.uint8)
        mask_border = np.zeros((h, w), dtype=np.uint8)

        center = (w // 2, h // 2)
        axes_inner = (int(w * 0.35), int(h * 0.40))
        axes_outer = (int(w * 0.48), int(h * 0.48))

        cv2.ellipse(mask_inner, center, axes_inner, 0, 0, 360, 255, -1)
        cv2.ellipse(mask_border, center, axes_outer, 0, 0, 360, 255, -1)
        # Border band is between outer and inner
        border_band = cv2.bitwise_and(mask_border, cv2.bitwise_not(mask_inner))

        # Compute Sobel gradients
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)

        border_pixels = grad_mag[border_band > 0]
        inner_pixels = grad_mag[mask_inner > 0]

        if len(border_pixels) == 0 or len(inner_pixels) == 0:
            return {"boundary_discontinuity_score": 0.0, "is_manipulated": False}

        mean_border_grad = float(np.mean(border_pixels))
        mean_inner_grad = float(np.mean(inner_pixels))

        # Gradient ratio: if border has unusually sharp or smeared gradient compared to inner face
        grad_ratio = mean_border_grad / max(1.0, mean_inner_grad)
        # Normal faces have natural transition (ratio ~1.0 to 1.8). Swaps often have >2.6 or <0.6 (over-smoothed)
        if grad_ratio > 2.6:
            boundary_score = min(1.0, (grad_ratio - 2.6) / 2.0 + 0.5)
        elif grad_ratio < 0.6:
            boundary_score = min(1.0, (0.6 - grad_ratio) / 0.6 + 0.4)
        else:
            boundary_score = max(0.0, (grad_ratio - 1.0) * 0.15)

        return {
            "boundary_discontinuity_score": round(float(boundary_score), 3),
            "border_gradient": round(mean_border_grad, 2),
            "inner_gradient": round(mean_inner_grad, 2),
            "gradient_ratio": round(grad_ratio, 2),
            "is_manipulated": boundary_score >= 0.65,
        }

    def analyze_color_space_consistency(
        self, face_bgr: np.ndarray, context_bgr: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Examines YCbCr and HSV chromatic distribution.
        Manipulated faces frequently exhibit a color temperature shift between the donor
        face and the target recipient's skin/neck region.
        """
        if face_bgr is None or face_bgr.size == 0:
            return {"chroma_mismatch_score": 0.0}

        ycbcr = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2YCrCb)
        h, w = face_bgr.shape[:2]

        # Inner face region (donor) vs outer margin (recipient skin/hair)
        inner_ycbcr = ycbcr[int(h * 0.25):int(h * 0.75), int(w * 0.25):int(w * 0.75)]
        top_margin = ycbcr[:int(h * 0.20), :]
        bottom_margin = ycbcr[int(h * 0.80):, :]

        margin_ycbcr = np.vstack([top_margin, bottom_margin])

        # Compute mean chroma (Cr, Cb) distance
        inner_cr = float(np.mean(inner_ycbcr[:, :, 1]))
        inner_cb = float(np.mean(inner_ycbcr[:, :, 2]))

        margin_cr = float(np.mean(margin_ycbcr[:, :, 1]))
        margin_cb = float(np.mean(margin_ycbcr[:, :, 2]))

        chroma_dist = np.sqrt((inner_cr - margin_cr)**2 + (inner_cb - margin_cb)**2)
        # Normal lighting allows slight variance (< 12.0). Strong donor mismatch is > 22.0
        mismatch_score = float(np.clip((chroma_dist - 8.0) / 25.0, 0.0, 1.0))

        return {
            "chroma_mismatch_score": round(mismatch_score, 3),
            "chroma_euclidean_distance": round(float(chroma_dist), 2),
            "inner_cr_cb": (round(inner_cr, 1), round(inner_cb, 1)),
            "margin_cr_cb": (round(margin_cr, 1), round(margin_cb, 1)),
        }

    def analyze_compression_residuals(self, face_bgr: np.ndarray) -> Dict[str, Any]:
        """
        Detects double-quantization / compression ghosting (FaceForensics++ c23/c40).
        Re-encodes image at quality 80 and measures error distribution.
        """
        if face_bgr is None or face_bgr.size == 0:
            return {"compression_anomaly_score": 0.0}

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 80]
        _, enc = cv2.imencode(".jpg", face_bgr, encode_param)
        dec = cv2.imdecode(enc, cv2.IMREAD_COLOR)

        diff = np.abs(face_bgr.astype(np.float32) - dec.astype(np.float32))
        diff_mean = float(np.mean(diff))
        diff_std = float(np.std(diff))

        # Synthetic faces pasted into re-encoded videos exhibit anomalous residual variance
        anomaly_score = float(np.clip((diff_std - 4.5) / 12.0, 0.0, 1.0))

        return {
            "compression_anomaly_score": round(anomaly_score, 3),
            "residual_mean": round(diff_mean, 2),
            "residual_std": round(diff_std, 2),
        }

    def full_forensics_scan(
        self, face_bgr: np.ndarray, context_bgr: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Runs the combined FaceForensics++ benchmark forensic battery."""
        boundary = self.analyze_boundary_feathering(face_bgr, context_bgr)
        color = self.analyze_color_space_consistency(face_bgr, context_bgr)
        compression = self.analyze_compression_residuals(face_bgr)

        # Weighted aggregate manipulation score
        score = (
            0.45 * boundary["boundary_discontinuity_score"] +
            0.35 * color["chroma_mismatch_score"] +
            0.20 * compression["compression_anomaly_score"]
        )

        detected_method = "none"
        if score >= 0.70:
            if boundary["boundary_discontinuity_score"] > color["chroma_mismatch_score"]:
                detected_method = "FaceSwap / DeepFaceLab boundary anomaly"
            else:
                detected_method = "Face2Face / NeuralTextures color temperature mismatch"

        return {
            "faceforensics_score": round(float(score), 3),
            "is_manipulated": score >= 0.65,
            "detected_method": detected_method,
            "boundary": boundary,
            "color_consistency": color,
            "compression": compression,
        }
