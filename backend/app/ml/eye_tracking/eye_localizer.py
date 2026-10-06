"""
Privacy Eye — Stage A: Precision Eye Localization, Orbital Landmark Modeling & Quality Gating
Tracks left and right eyes dynamically across video frames, computes 6-point orbital landmarks,
derives Eye Aspect Ratio (EAR), and enforces strict visibility and quality gatekeeping.
"""
import math
import time
from typing import Dict, Any, List, Optional, Tuple
import cv2
import numpy as np

from app.ml.configs.eye_blink_config import (
    EyeVisibilityState,
    EyeBlinkConfig,
    DEFAULT_CONFIG,
)


class EyeLocalizer:
    """
    Real-time Eye Localization, Anatomical Landmark Derivation & Quality Engine.
    Dynamically follows face tracking across frames, preventing eye identity confusion.
    """

    def __init__(self, config: Optional[EyeBlinkConfig] = None):
        self.config = config or DEFAULT_CONFIG
        # Temporal smoothing state per session: session_id -> state
        self._tracks: Dict[str, Dict[str, Any]] = {}

    def _init_session_track(self, session_id: str) -> Dict[str, Any]:
        return {
            "last_seen_time": time.time(),
            "left_center_smoothed": None,
            "right_center_smoothed": None,
            "left_ear_history": [],
            "right_ear_history": [],
            "baseline_ear": self.config.DEFAULT_BASELINE_EAR,
        }

    def compute_ear_from_landmarks(self, landmarks_6pt: List[List[float]]) -> float:
        """
        Calculates Eye Aspect Ratio (EAR) based on Soukupová & Čech (2016):
        EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)
        """
        if len(landmarks_6pt) < 6:
            return 0.0

        p1 = np.array(landmarks_6pt[0], dtype=np.float32)
        p2 = np.array(landmarks_6pt[1], dtype=np.float32)
        p3 = np.array(landmarks_6pt[2], dtype=np.float32)
        p4 = np.array(landmarks_6pt[3], dtype=np.float32)
        p5 = np.array(landmarks_6pt[4], dtype=np.float32)
        p6 = np.array(landmarks_6pt[5], dtype=np.float32)

        d_v1 = float(np.linalg.norm(p2 - p6))
        d_v2 = float(np.linalg.norm(p3 - p5))
        d_h = float(np.linalg.norm(p1 - p4))

        if d_h < 1e-4:
            return 0.0

        ear = (d_v1 + d_v2) / (2.0 * d_h)
        return float(ear)

    def derive_6pt_eye_landmarks(
        self,
        center_pt: List[int],
        iod: float,
        is_left_eye: bool,
        vertical_opening_factor: float = 1.0,
    ) -> Tuple[List[List[float]], List[int], Tuple[int, int]]:
        """
        Derives the 6 orbital contour landmarks from the eye center and interocular distance (IOD).
        p1: outer canthus
        p2, p3: superior palpebral margin (upper eyelid)
        p4: inner canthus
        p5, p6: inferior palpebral margin (lower eyelid)
        Returns (landmarks_6pt, bbox [x, y, w, h], center (cx, cy)).
        """
        cx, cy = float(center_pt[0]), float(center_pt[1])
        # Eye width is approximately 0.34 of IOD
        half_w = max(float(self.config.MIN_EYE_SIZE_PX), iod * 0.17)
        # Eye baseline open height is approximately 0.11 of IOD, scaled by opening factor
        base_h = max(2.0, iod * 0.11 * vertical_opening_factor)

        # Orientation: outer canthus is further away from nose, inner canthus closer to nose
        if is_left_eye:  # Subject's left eye (viewer's right)
            p1 = [cx + half_w, cy]                 # lateral canthus
            p4 = [cx - half_w, cy]                 # medial canthus
            p2 = [cx + half_w * 0.45, cy - base_h] # superior outer
            p3 = [cx - half_w * 0.45, cy - base_h] # superior inner
            p6 = [cx + half_w * 0.45, cy + base_h] # inferior outer
            p5 = [cx - half_w * 0.45, cy + base_h] # inferior inner
        else:  # Subject's right eye (viewer's left)
            p1 = [cx - half_w, cy]                 # lateral canthus
            p4 = [cx + half_w, cy]                 # medial canthus
            p2 = [cx - half_w * 0.45, cy - base_h] # superior outer
            p3 = [cx + half_w * 0.45, cy - base_h] # superior inner
            p6 = [cx - half_w * 0.45, cy + base_h] # inferior outer
            p5 = [cx + half_w * 0.45, cy + base_h] # inferior inner

        landmarks = [
            [round(pt[0], 1), round(pt[1], 1)]
            for pt in [p1, p2, p3, p4, p5, p6]
        ]

        # Calculate bounding box
        xs = [pt[0] for pt in landmarks]
        ys = [pt[1] for pt in landmarks]
        pad_x = half_w * 0.15
        pad_y = max(3.0, base_h * 0.25)

        bx = int(max(0, min(xs) - pad_x))
        by = int(max(0, min(ys) - pad_y))
        bw = int(max(xs) - min(xs) + 2 * pad_x)
        bh = int(max(ys) - min(ys) + 2 * pad_y)

        return landmarks, [bx, by, bw, bh], (int(cx), int(cy))

    def evaluate_ocular_patch(
        self,
        img_bgr: np.ndarray,
        bbox: List[int],
    ) -> Dict[str, Any]:
        """
        Analyzes eye patch for sharpness, contrast, lighting, glare, and sunglasses.
        """
        h, w = img_bgr.shape[:2]
        x, y, bw, bh = bbox
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(w, x + bw)
        y2 = min(h, y + bh)

        if (x2 - x1) < self.config.MIN_EYE_SIZE_PX or (y2 - y1) < (self.config.MIN_EYE_SIZE_PX - 4):
            return {
                "quality": 0.05,
                "is_sharp": False,
                "is_blurry": True,
                "is_sunglasses": False,
                "lap_var": 0.0,
                "contrast": 0.0,
                "mean_lum": 0.0,
                "vert_energy": 0.0,
            }

        crop = img_bgr[y1:y2, x1:x2]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

        # 1. Laplacian sharpness
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        lap_var = float(lap.var())
        is_sharp = lap_var >= self.config.MIN_BLUR_VAR

        # 2. Contrast
        contrast = float(np.std(gray))
        dynamic_range = float(np.max(gray) - np.min(gray))

        # 3. Illumination
        mean_lum = float(np.mean(gray))
        is_dark = mean_lum < 30.0
        is_glare = float(np.mean(gray > 240)) > 0.15

        # 4. Sunglasses detection
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        sat_mean = float(np.mean(hsv[:, :, 1]))
        val_mean = float(np.mean(hsv[:, :, 2]))
        is_sunglasses = (
            (val_mean < self.config.SUNGLASSES_MAX_VAL and sat_mean < self.config.SUNGLASSES_MAX_SAT)
            or (mean_lum < 50.0 and dynamic_range < 35.0)
        )

        # 5. Vertical eyelid edge energy for palpebral opening
        sob_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        vert_energy = float(np.mean(np.abs(sob_y)))

        # Quality index (0.0 to 1.0)
        q_sharp = min(1.0, lap_var / 80.0)
        q_contrast = min(1.0, contrast / 35.0)
        q_illum = 1.0 - (0.6 if is_dark else 0.0) - (0.4 if is_glare else 0.0)
        quality_score = max(0.0, min(1.0, (q_sharp * 0.45) + (q_contrast * 0.35) + (q_illum * 0.20)))

        if is_sunglasses:
            quality_score = min(quality_score, 0.20)

        return {
            "quality": round(quality_score, 3),
            "is_sharp": is_sharp,
            "is_blurry": not is_sharp,
            "is_sunglasses": is_sunglasses,
            "lap_var": round(lap_var, 1),
            "contrast": round(contrast, 1),
            "mean_lum": round(mean_lum, 1),
            "vert_energy": round(vert_energy, 2),
        }

    def localize_eyes(
        self,
        img_bgr: np.ndarray,
        landmarks: Optional[Dict[str, List[int]]],
        face_box: Optional[List[int]],
        head_yaw: float = 0.0,
        head_pitch: float = 0.0,
        session_id: str = "default_session",
    ) -> Dict[str, Any]:
        """
        Executes full eye localization, tracking, landmark generation, EAR computation,
        and quality gatekeeping.
        """
        now = time.time()
        if session_id not in self._tracks:
            self._tracks[session_id] = self._init_session_track(session_id)
        track = self._tracks[session_id]

        # Check for missing face or landmarks
        if not landmarks or not face_box:
            return self._build_empty_result(reason="No face or landmarks in frame")

        re_pt = landmarks.get("right_eye")
        le_pt = landmarks.get("left_eye")
        if not re_pt or not le_pt:
            return self._build_empty_result(reason="Eye centers not located")

        # Interocular distance
        iod = max(10.0, float(math.hypot(le_pt[0] - re_pt[0], le_pt[1] - re_pt[1])))

        # Temporal smoothing for eye centers to follow smooth head movement
        alpha = 0.65
        if track["left_center_smoothed"] is None:
            track["left_center_smoothed"] = [float(le_pt[0]), float(le_pt[1])]
            track["right_center_smoothed"] = [float(re_pt[0]), float(re_pt[1])]
        else:
            track["left_center_smoothed"][0] = alpha * le_pt[0] + (1 - alpha) * track["left_center_smoothed"][0]
            track["left_center_smoothed"][1] = alpha * le_pt[1] + (1 - alpha) * track["left_center_smoothed"][1]
            track["right_center_smoothed"][0] = alpha * re_pt[0] + (1 - alpha) * track["right_center_smoothed"][0]
            track["right_center_smoothed"][1] = alpha * re_pt[1] + (1 - alpha) * track["right_center_smoothed"][1]

        smoothed_le = [int(round(track["left_center_smoothed"][0])), int(round(track["left_center_smoothed"][1]))]
        smoothed_re = [int(round(track["right_center_smoothed"][0])), int(round(track["right_center_smoothed"][1]))]

        # Initial bounding boxes for quality inspection
        _, left_box_init, _ = self.derive_6pt_eye_landmarks(smoothed_le, iod, is_left_eye=True)
        _, right_box_init, _ = self.derive_6pt_eye_landmarks(smoothed_re, iod, is_left_eye=False)

        q_left = self.evaluate_ocular_patch(img_bgr, left_box_init)
        q_right = self.evaluate_ocular_patch(img_bgr, right_box_init)

        # Derive vertical eyelid opening factor from edge energy
        # Typical vertical energy: 8.0 - 25.0 when open; < 5.0 when closed
        left_open_factor = max(0.20, min(1.40, q_left["vert_energy"] / 14.0))
        right_open_factor = max(0.20, min(1.40, q_right["vert_energy"] / 14.0))

        # Full 6-point landmarks derived with dynamic eyelid contour
        left_lms, left_box, left_center = self.derive_6pt_eye_landmarks(
            smoothed_le, iod, is_left_eye=True, vertical_opening_factor=left_open_factor
        )
        right_lms, right_box, right_center = self.derive_6pt_eye_landmarks(
            smoothed_re, iod, is_left_eye=False, vertical_opening_factor=right_open_factor
        )

        left_ear = self.compute_ear_from_landmarks(left_lms)
        right_ear = self.compute_ear_from_landmarks(right_lms)
        mean_ear = float((left_ear + right_ear) / 2.0)

        # Visibility classification
        left_visible = q_left["quality"] >= self.config.MIN_EYE_QUALITY and not q_left["is_sunglasses"]
        right_visible = q_right["quality"] >= self.config.MIN_EYE_QUALITY and not q_right["is_sunglasses"]

        # Handle extreme yaw hiding one eye
        if head_yaw < -0.28:
            right_visible = False
        elif head_yaw > +0.28:
            left_visible = False

        is_obscured = q_left["is_sunglasses"] or q_right["is_sunglasses"]
        is_blurry = q_left["is_blurry"] and q_right["is_blurry"]

        if is_obscured:
            visibility_state = EyeVisibilityState.NONE_VISIBLE
            visibility_label = "EYES_OBSCURED"
            eye_visibility_score = 0.0
        elif is_blurry:
            visibility_state = EyeVisibilityState.LOW_QUALITY
            visibility_label = "EYE_TOO_BLURRY"
            eye_visibility_score = 0.20
        elif left_visible and right_visible:
            visibility_state = EyeVisibilityState.BOTH_VISIBLE
            visibility_label = "BOTH_EYES_VISIBLE"
            eye_visibility_score = 1.0
        elif left_visible and not right_visible:
            visibility_state = EyeVisibilityState.LEFT_ONLY
            visibility_label = "LEFT_ONLY"
            eye_visibility_score = 0.70
        elif right_visible and not left_visible:
            visibility_state = EyeVisibilityState.RIGHT_ONLY
            visibility_label = "RIGHT_ONLY"
            eye_visibility_score = 0.70
        else:
            visibility_state = EyeVisibilityState.NONE_VISIBLE
            visibility_label = "BOTH_EYES_NOT_VISIBLE"
            eye_visibility_score = 0.0

        overall_quality = round(float((q_left["quality"] + q_right["quality"]) / 2.0), 3)
        landmark_confidence = round(float(min(1.0, (iod / 60.0) * overall_quality)), 3)

        return {
            "eye_visibility_state": visibility_state,
            "eye_visibility_label": visibility_label,
            "eye_visibility_score": eye_visibility_score,
            "overall_eye_quality": overall_quality,
            "landmark_confidence": landmark_confidence,
            "is_blurry": bool(is_blurry),
            "is_obscured": bool(is_obscured),
            "interocular_distance": round(iod, 1),
            # Left Eye Attributes
            "left_eye": {
                "visible": bool(left_visible),
                "landmarks": left_lms,
                "bbox": left_box,
                "center": list(left_center),
                "width": left_box[2],
                "height": left_box[3],
                "ear": round(left_ear, 3),
                "quality": q_left["quality"],
                "lap_var": q_left["lap_var"],
                "is_sharp": q_left["is_sharp"],
                "vert_energy": q_left["vert_energy"],
            },
            # Right Eye Attributes
            "right_eye": {
                "visible": bool(right_visible),
                "landmarks": right_lms,
                "bbox": right_box,
                "center": list(right_center),
                "width": right_box[2],
                "height": right_box[3],
                "ear": round(right_ear, 3),
                "quality": q_right["quality"],
                "lap_var": q_right["lap_var"],
                "is_sharp": q_right["is_sharp"],
                "vert_energy": q_right["vert_energy"],
            },
            "mean_ear": round(mean_ear, 3),
        }

    def _build_empty_result(self, reason: str) -> Dict[str, Any]:
        return {
            "eye_visibility_state": EyeVisibilityState.NONE_VISIBLE,
            "eye_visibility_label": "BOTH_EYES_NOT_VISIBLE",
            "eye_visibility_score": 0.0,
            "overall_eye_quality": 0.0,
            "landmark_confidence": 0.0,
            "is_blurry": False,
            "is_obscured": False,
            "interocular_distance": 0.0,
            "left_eye": {
                "visible": False,
                "landmarks": [],
                "bbox": [0, 0, 0, 0],
                "center": [0, 0],
                "width": 0,
                "height": 0,
                "ear": 0.0,
                "quality": 0.0,
                "lap_var": 0.0,
                "is_sharp": False,
                "vert_energy": 0.0,
            },
            "right_eye": {
                "visible": False,
                "landmarks": [],
                "bbox": [0, 0, 0, 0],
                "center": [0, 0],
                "width": 0,
                "height": 0,
                "ear": 0.0,
                "quality": 0.0,
                "lap_var": 0.0,
                "is_sharp": False,
                "vert_energy": 0.0,
            },
            "mean_ear": 0.0,
            "reason": reason,
        }
