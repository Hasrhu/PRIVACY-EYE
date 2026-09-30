"""
Privacy Eye — Screen, Phone & Presentation Attack Detection Engine
Differentiates between a phone present elsewhere in the scene (Case A: human holding phone)
versus a phone/screen physically displaying the target face (Case B: presentation attack).
"""
import math
import numpy as np
import cv2
from typing import Dict, Any, List, Optional, Tuple


class ScreenDetector:
    """
    Multimodal Display & Presentation Attack Detector.
    Evaluates geometric rectangular bezels, Moiré frequency harmonics,
    specular display reflections, and screen-to-face spatial association.
    """

    def __init__(self, attack_threshold: float = 0.75):
        self.attack_threshold = attack_threshold

    def detect_display_bezels(
        self, img_bgr: np.ndarray
    ) -> List[Dict[str, Any]]:
        """
        Detects rectangular smartphone, tablet, laptop, or monitor screens in the frame
        using multi-scale edge contours, polygon approximation, and aspect-ratio filters.
        """
        h, w = img_bgr.shape[:2]
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        # Bilateral filter preserves sharp screen bezel edges while smoothing interior textures
        blurred = cv2.bilateralFilter(gray, 7, 50, 50)
        edges = cv2.Canny(blurred, 30, 100)

        # Dilate slightly to connect segmented bezel corners
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=1)

        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        detected_screens = []

        min_screen_area = (w * h) * 0.04   # Screen must occupy at least 4% of frame
        max_screen_area = (w * h) * 0.98

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_screen_area or area > max_screen_area:
                continue

            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.03 * peri, True)

            # Screens are quadrilateral (4 vertices) or convex rectangles
            if len(approx) == 4 and cv2.isContourConvex(approx):
                bx, by, bw, bh = cv2.boundingRect(approx)
                aspect = float(bw) / float(bh) if bh > 0 else 1.0

                # Smartphone, tablet, laptop, monitor (aspect ratio 0.38 to 2.65)
                is_display_aspect = (0.38 <= aspect <= 2.65)
                if not is_display_aspect:
                    continue

                # Check edge gradient contrast along the perimeter
                mask = np.zeros(gray.shape, dtype=np.uint8)
                cv2.drawContours(mask, [approx], -1, 255, 2)
                edge_intensity = float(np.mean(gray[mask > 0]))

                # Calculate screen confidence based on geometric rectangularity
                rect_area = bw * bh
                extent = float(area) / float(rect_area) if rect_area > 0 else 0.0
                if extent < 0.72:
                    continue

                device_type = "SMARTPHONE" if (0.42 <= aspect <= 0.65 or 1.55 <= aspect <= 2.35) else "SCREEN_OR_TABLET"
                screen_conf = min(0.98, round(0.60 + (extent * 0.25) + min(0.15, area / (w * h)), 2))

                detected_screens.append({
                    "box": [bx, by, bw, bh],
                    "polygon": approx.tolist(),
                    "device_type": device_type,
                    "confidence": screen_conf,
                    "aspect_ratio": round(aspect, 2),
                    "area_pct": round((area / (w * h)) * 100.0, 1),
                })

        # Non-maximum suppression by bounding box IoU
        detected_screens = self._nms_screens(detected_screens)
        return detected_screens

    def _nms_screens(self, screens: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(screens) <= 1:
            return screens
        screens = sorted(screens, key=lambda s: s["confidence"], reverse=True)
        keep = []
        for s in screens:
            box_a = s["box"]
            overlap = False
            for k in keep:
                box_b = k["box"]
                iou = self.calculate_iou(box_a, box_b)
                if iou > 0.45:
                    overlap = True
                    break
            if not overlap:
                keep.append(s)
        return keep

    @staticmethod
    def calculate_iou(box_a: List[int], box_b: List[int]) -> float:
        xa = max(box_a[0], box_b[0])
        ya = max(box_a[1], box_b[1])
        xb = min(box_a[0] + box_a[2], box_b[0] + box_b[2])
        yb = min(box_a[1] + box_a[3], box_b[1] + box_b[3])
        inter = max(0, xb - xa) * max(0, yb - ya)
        area_a = box_a[2] * box_a[3]
        area_b = box_b[2] * box_b[3]
        union = area_a + area_b - inter
        return float(inter / union) if union > 0 else 0.0

    @staticmethod
    def calculate_iof(face_box: List[int], screen_box: List[int]) -> float:
        """
        Intersection-over-Face (IoF): what percentage of the face is inside the screen.
        """
        fx, fy, fw, fh = face_box
        sx, sy, sw, sh = screen_box

        xa = max(fx, sx)
        ya = max(fy, sy)
        xb = min(fx + fw, sx + sw)
        yb = min(fy + fh, sy + sh)

        inter = max(0, xb - xa) * max(0, yb - ya)
        face_area = fw * fh
        return float(inter / face_area) if face_area > 0 else 0.0

    def compute_moire_and_specular_signals(
        self, face_crop_bgr: np.ndarray
    ) -> Dict[str, float]:
        """
        Computes 2D FFT Moiré high-frequency grid energy and specular reflection spikes.
        """
        if face_crop_bgr.shape[0] < 30 or face_crop_bgr.shape[1] < 30:
            return {"moire_score": 0.0, "specular_score": 0.0}

        gray = cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape[:2]

        # 1. 2D FFT for periodic screen subpixel patterns
        f = np.fft.fft2(gray.astype(np.float32))
        fshift = np.fft.fftshift(f)
        magnitude = 20 * np.log(np.abs(fshift) + 1.0)

        # Sample high-frequency outer perimeter
        cy, cx = h // 2, w // 2
        r_inner = int(min(cy, cx) * 0.40)
        y, x = np.ogrid[:h, :w]
        mask_outer = ((x - cx) ** 2 + (y - cy) ** 2) >= (r_inner ** 2)

        hf_mean = float(np.mean(magnitude[mask_outer]))
        lf_mean = float(np.mean(magnitude[~mask_outer]))
        ratio = hf_mean / max(lf_mean, 1.0)
        # Ratio typically ~0.35-0.55 for natural skin, >= 0.70 for digital screens
        moire_score = max(0.0, min(1.0, (ratio - 0.45) / 0.35))

        # 2. Specular glass reflections (harsh saturated white glare spots on display glass)
        hsv = cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2HSV)
        val = hsv[:, :, 2]
        sat = hsv[:, :, 1]
        glare_pixels = (val > 245) & (sat < 35)
        glare_ratio = float(np.mean(glare_pixels))
        specular_score = max(0.0, min(1.0, glare_ratio * 25.0))

        return {
            "moire_score": round(moire_score, 3),
            "specular_score": round(specular_score, 3),
        }

    def analyze(
        self,
        img_bgr: np.ndarray,
        face_box: Optional[List[int]],
        temporal_jitter: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Executes screen detection, screen-face association, and presentation attack scoring.
        """
        screens = self.detect_display_bezels(img_bgr)
        phone_in_scene = len(screens) > 0

        if not face_box:
            return {
                "phone_detected": phone_in_scene,
                "screen_face_associated": False,
                "presentation_attack": False,
                "phone_object_confidence": max([s["confidence"] for s in screens], default=0.0),
                "screen_face_association_confidence": 0.0,
                "presentation_attack_confidence": 0.0,
                "associated_screen": None,
                "detected_screens": screens,
                "reason_codes": ["PHONE_DETECTED"] if phone_in_scene else [],
                "user_message": "Mobile device present in scene" if phone_in_scene else None,
            }

        fx, fy, fw, fh = face_box
        face_crop = img_bgr[fy : fy + fh, fx : fx + fw]
        signals = self.compute_moire_and_specular_signals(face_crop)

        best_associated_screen = None
        max_iof = 0.0

        for s in screens:
            iof = self.calculate_iof(face_box, s["box"])
            if iof > max_iof:
                max_iof = iof
                best_associated_screen = s

        # Crucial Association Rule: Face must be INSIDE screen (IoF >= 0.70)
        face_inside_screen = bool(max_iof >= 0.70)

        screen_conf = best_associated_screen["confidence"] if best_associated_screen else 0.0
        assoc_conf = round(float(max_iof), 2)

        # Presentation Attack Confidence:
        # High only when face is INSIDE screen AND physical display signals (Moiré / Specular / Bezel) confirm it
        if face_inside_screen:
            # Base geometric presentation score from screen detector and face-inside-screen containment
            geo_evidence = (screen_conf * 0.45) + (assoc_conf * 0.45)
            # Physical display artifact boosters (Moiré pattern and specular glass glare)
            artifact_boost = (signals["moire_score"] * 0.10) + (signals["specular_score"] * 0.10)
            phys_evidence = geo_evidence + artifact_boost

            if temporal_jitter < 0.20:
                phys_evidence = min(1.0, phys_evidence + 0.10)

            presentation_attack_confidence = round(float(min(0.99, phys_evidence)), 2)
            is_attack = presentation_attack_confidence >= self.attack_threshold
        else:
            # Case A: Phone is in scene, but face is NOT inside phone!
            presentation_attack_confidence = round(float(signals["moire_score"] * 0.25), 2)
            is_attack = False

        reason_codes = []
        user_message = None

        if is_attack:
            reason_codes.append("PHONE_PRESENTATION_DETECTED")
            reason_codes.append("SCREEN_FACE_DETECTED")
            user_message = "A face appears to be displayed through a phone or electronic screen."
        elif phone_in_scene:
            reason_codes.append("PHONE_IN_SCENE_IRRELEVANT")
            user_message = "Electronic device detected in scene (Direct human face verified)."

        return {
            "phone_detected": phone_in_scene,
            "screen_face_associated": face_inside_screen,
            "presentation_attack": is_attack,
            "phone_object_confidence": screen_conf,
            "screen_face_association_confidence": assoc_conf,
            "presentation_attack_confidence": presentation_attack_confidence,
            "moire_score": signals["moire_score"],
            "specular_score": signals["specular_score"],
            "associated_screen": best_associated_screen,
            "detected_screens": screens,
            "reason_codes": reason_codes,
            "user_message": user_message,
        }


# Global singleton instance
screen_detector = ScreenDetector()
