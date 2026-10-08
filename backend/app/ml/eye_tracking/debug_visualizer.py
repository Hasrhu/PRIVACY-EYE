"""
Privacy Eye — Part 17: Development Visual Debug Mode
Overlays face bounding boxes, 6-point eye contours, ocular bounding boxes,
EAR telemetry and confidence indicators for forensic inspection.
"""
from typing import Dict, Any, Optional
import cv2
import numpy as np


class EyeDebugVisualizer:
    """
    Renders visual debug overlays onto camera frames for testing and development.
    Disabled by default in production.
    """

    @staticmethod
    def draw_debug_overlay(
        img_bgr: np.ndarray,
        face_box: Optional[list],
        eye_data: Dict[str, Any],

        fps: float = 30.0,
    ) -> np.ndarray:
        """
        Draws anatomical landmarks, bounding boxes, and EAR telemetry.
        """
        canvas = img_bgr.copy()
        h, w = canvas.shape[:2]

        # 1. Face Bounding Box
        if face_box and len(face_box) == 4:
            fx, fy, fw, fh = [int(v) for v in face_box]
            cv2.rectangle(canvas, (fx, fy), (fx + fw, fy + fh), (0, 240, 255), 1)

        # 2. Eye Bounding Boxes & Landmarks
        left_eye = eye_data.get("left_eye", {})
        right_eye = eye_data.get("right_eye", {})

        for eye, color in [(left_eye, (0, 255, 128)), (right_eye, (255, 128, 0))]:
            bbox = eye.get("bbox")
            if bbox and len(bbox) == 4 and bbox[2] > 0 and bbox[3] > 0:
                bx, by, bw, bh = [int(v) for v in bbox]
                cv2.rectangle(canvas, (bx, by), (bx + bw, by + bh), color, 1)

            # Draw 6-point orbital landmarks
            lms = eye.get("landmarks", [])
            for pt in lms:
                if len(pt) == 2:
                    cv2.circle(canvas, (int(pt[0]), int(pt[1])), 2, (0, 255, 255), -1)

            center = eye.get("center")
            if center and len(center) == 2 and center[0] > 0:
                cv2.circle(canvas, (int(center[0]), int(center[1])), 3, (0, 0, 255), -1)

        # 3. Telemetry Glass Panel (Top Left)
        panel_w = 280
        panel_h = 165
        overlay = canvas.copy()
        cv2.rectangle(overlay, (10, 10), (10 + panel_w, 10 + panel_h), (15, 20, 30), -1)
        cv2.addWeighted(overlay, 0.75, canvas, 0.25, 0, canvas)
        cv2.rectangle(canvas, (10, 10), (10 + panel_w, 10 + panel_h), (70, 85, 110), 1)

        # Text Lines
        l_ear = float(left_eye.get("ear", eye_data.get("left_ear", 0.0)))
        r_ear = float(right_eye.get("ear", eye_data.get("right_ear", 0.0)))
        left_state = eye_data.get("left_eye_state", "OPEN")
        right_state = eye_data.get("right_eye_state", "OPEN")
        quality = eye_data.get("overall_eye_quality", 0.0)

        lines = [
            (f"PRIVACY EYE — OCULAR DEBUG", (0, 240, 255)),
            (f"LEFT EYE: {left_state} (EAR: {l_ear:.3f})", (0, 255, 128) if left_state == "OPEN" else (0, 180, 255)),
            (f"RIGHT EYE: {right_state} (EAR: {r_ear:.3f})", (0, 255, 128) if right_state == "OPEN" else (0, 180, 255)),
        ]

        y_offset = 32
        for text, color in lines:
            cv2.putText(
                canvas,
                text,
                (20, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.40,
                color,
                1,
                cv2.LINE_AA,
            )
            y_offset += 22

        return canvas
