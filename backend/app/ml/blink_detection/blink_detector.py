"""
Privacy Eye — Production-Quality Blink Detection Module
References: 
- https://github.com/Pushtogithub23/Eye-Blink-Detection-using-MediaPipe-and-OpenCV
- https://github.com/Praneesh-Gattadi/BLINK_DETECTION_SYSTEM
- https://github.com/LAIR-Lab/Blink-Detection

MIT License retained for code patterns originating from the above repositories.
"""

import cv2
import math
import numpy as np
import mediapipe as mp
from typing import Dict, Any

# Mediapipe Face Mesh indices for eyes
LEFT_EYE_INDICES = [33, 160, 158, 133, 153, 144]
RIGHT_EYE_INDICES = [362, 385, 387, 263, 373, 380]

class MediaPipeBlinkDetector:
    """
    Extracts precise facial landmarks using MediaPipe Face Mesh and calculates 
    the Eye Aspect Ratio (EAR). Incorporates stability checks to reject false 
    blinks caused by motion blur or tracking loss.
    """
    def __init__(self):
        try:
            self.mp_face_mesh = mp.solutions.face_mesh
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            )
        except AttributeError:
            self.mp_face_mesh = None
            self.face_mesh = None
            
        # State tracking for face stability check
        self.prev_face_center = {}
        self.prev_face_width = {}

    def _calculate_ear(self, eye_points: list, landmarks: list, w: int, h: int) -> float:
        """
        Calculates Eye Aspect Ratio: (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
        """
        try:
            p1 = np.array([landmarks[eye_points[0]].x * w, landmarks[eye_points[0]].y * h])
            p2 = np.array([landmarks[eye_points[1]].x * w, landmarks[eye_points[1]].y * h])
            p3 = np.array([landmarks[eye_points[2]].x * w, landmarks[eye_points[2]].y * h])
            p4 = np.array([landmarks[eye_points[3]].x * w, landmarks[eye_points[3]].y * h])
            p5 = np.array([landmarks[eye_points[4]].x * w, landmarks[eye_points[4]].y * h])
            p6 = np.array([landmarks[eye_points[5]].x * w, landmarks[eye_points[5]].y * h])
        except IndexError:
            return 0.0

        vertical1 = np.linalg.norm(p2 - p6)
        vertical2 = np.linalg.norm(p3 - p5)
        horizontal = np.linalg.norm(p1 - p4)
        
        if horizontal == 0:
            return 0.0
        return (vertical1 + vertical2) / (2.0 * horizontal)

    def analyze_eyes(self, session_id: str, img_bgr: np.ndarray) -> Dict[str, Any]:
        """
        Extracts MediaPipe landmarks and computes EAR and face stability.
        Outputs data for the evidence-fusion engine and blink state machine.
        """
        h, w, _ = img_bgr.shape
        rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        
        # Base state representing no visibility/tracking
        eye_analysis = {
            "eye_status": "NONE_VISIBLE",
            "overall_eye_quality": 0.0,
            "is_blurry": False,
            "is_obscured": False,
            "mean_ear": 0.0,
            "left_ear": 0.0,
            "right_ear": 0.0,
            "openness": 0.0,
            "face_detected": False,
            "left_eye_visible": False,
            "right_eye_visible": False
        }
        
        if self.face_mesh is None:
            return eye_analysis
            
        results = self.face_mesh.process(rgb)
        
        if results.multi_face_landmarks:
            eye_analysis["face_detected"] = True
            mesh = results.multi_face_landmarks[0]
            
            left_ear = self._calculate_ear(LEFT_EYE_INDICES, mesh.landmark, w, h)
            right_ear = self._calculate_ear(RIGHT_EYE_INDICES, mesh.landmark, w, h)
            mean_ear = (left_ear + right_ear) / 2.0
            
            # Simple motion stability check
            xs = [lm.x * w for lm in mesh.landmark]
            ys = [lm.y * h for lm in mesh.landmark]
            cx = sum(xs) / len(xs)
            cy = sum(ys) / len(ys)
            face_width = max(xs) - min(xs)
            
            movement_ratio = 0.0
            if session_id in self.prev_face_center and session_id in self.prev_face_width:
                dx = cx - self.prev_face_center[session_id][0]
                dy = cy - self.prev_face_center[session_id][1]
                move_px = math.hypot(dx, dy)
                prev_w = self.prev_face_width[session_id]
                movement_ratio = move_px / max(1.0, prev_w)
            
            self.prev_face_center[session_id] = (cx, cy)
            self.prev_face_width[session_id] = face_width
            
            # Determine visibility & quality
            if movement_ratio > 0.08:  # Motion stability check (rejects motion-blur false blinks)
                eye_analysis["is_blurry"] = True
                eye_analysis["overall_eye_quality"] = 0.3
                eye_analysis["eye_status"] = "EYE_TOO_BLURRY"
            elif mean_ear < 0.05 and left_ear < 0.05 and right_ear < 0.05:
                # Potential tracking loss / occluded
                eye_analysis["is_obscured"] = True
                eye_analysis["overall_eye_quality"] = 0.2
            else:
                eye_analysis["eye_status"] = "BOTH_EYES_VISIBLE"
                eye_analysis["overall_eye_quality"] = 0.95
                eye_analysis["is_blurry"] = False
                eye_analysis["is_obscured"] = False
                eye_analysis["left_eye_visible"] = True
                eye_analysis["right_eye_visible"] = True
                
            eye_analysis["mean_ear"] = mean_ear
            eye_analysis["left_ear"] = left_ear
            eye_analysis["right_ear"] = right_ear
            eye_analysis["openness"] = mean_ear
                
        return eye_analysis
