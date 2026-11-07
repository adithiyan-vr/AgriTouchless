"""
gesture_engine.py
AgriTouchless: Farm & Kitchen Hygiene Controller
Member 1: Computer Vision & Gesture Lead (Adithiyan V R)
"""

import math
from typing import List, Dict, Tuple, Optional
import cv2
import mediapipe as mp


class GestureEngine:
    """
    Core Computer Vision & Hand Landmark Processing Engine powered by MediaPipe.
    Extracts 21 3D hand landmarks, applies palm-relative distance normalization,
    and classifies static poses (OPEN_PALM vs. CLOSED_FIST).
    """

    # Hand Landmark Indices (MediaPipe)
    WRIST = 0
    THUMB_CMC = 1
    THUMB_MCP = 2
    THUMB_IP = 3
    THUMB_TIP = 4

    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_DIP = 7
    INDEX_TIP = 8

    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_DIP = 11
    MIDDLE_TIP = 12

    RING_MCP = 13
    RING_PIP = 14
    RING_DIP = 15
    RING_TIP = 16

    PINKY_MCP = 17
    PINKY_PIP = 18
    PINKY_DIP = 19
    PINKY_TIP = 20

    FINGERTIP_IDS = [INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]
    PIP_IDS = [INDEX_PIP, MIDDLE_PIP, RING_PIP, PINKY_PIP]

    def __init__(self,
                 max_num_hands: int = 2,
                 min_detection_confidence: float = 0.7,
                 min_tracking_confidence: float = 0.5):
        """
        Initialize the MediaPipe Hands pipeline.
        """
        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence
        )

    def process_frame(self, frame_bgr):
        """
        Convert BGR frame to RGB and process with MediaPipe Hands.
        """
        rgb_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = self.hands.process(rgb_frame)
        rgb_frame.flags.writeable = True
        return results

    def extract_landmarks(self, hand_landmarks, width: int = 1280, height: int = 720) -> List[Dict[str, float]]:
        """
        Extract 21 landmarks into standard dictionary list containing
        both normalized (0.0 - 1.0) and absolute pixel coordinates.
        """
        landmarks = []
        for idx, lm in enumerate(hand_landmarks.landmark):
            landmarks.append({
                "id": idx,
                "x": lm.x,
                "y": lm.y,
                "z": lm.z,
                "px": int(lm.x * width),
                "py": int(lm.y * height)
            })
        return landmarks

    def normalize_landmarks(self, landmarks: List[Dict[str, float]]) -> List[Dict[str, float]]:
        """
        Distance-Independent Normalization:
        Translates coordinates relative to Wrist (ID 0) and scales by palm distance:
        d_palm = sqrt((x9 - x0)^2 + (y9 - y0)^2)
        Ensures gesture recognition operates reliably regardless of user distance (1m - 2m).
        """
        if not landmarks or len(landmarks) < 21:
            return landmarks

        wrist = landmarks[self.WRIST]
        middle_mcp = landmarks[self.MIDDLE_MCP]

        # Calculate Euclidean palm reference distance
        dx = middle_mcp["x"] - wrist["x"]
        dy = middle_mcp["y"] - wrist["y"]
        d_palm = math.sqrt(dx * dx + dy * dy)
        if d_palm < 1e-5:
            d_palm = 1.0

        normalized = []
        for lm in landmarks:
            norm_x = (lm["x"] - wrist["x"]) / d_palm
            norm_y = (lm["y"] - wrist["y"]) / d_palm
            norm_z = (lm["z"] - wrist["z"]) / d_palm
            normalized.append({
                "id": lm["id"],
                "norm_x": norm_x,
                "norm_y": norm_y,
                "norm_z": norm_z,
                "px": lm["px"],
                "py": lm["py"],
                "raw_x": lm["x"],
                "raw_y": lm["y"]
            })
        return normalized

    def classify_hand_pose(self, landmarks: List[Dict[str, float]]) -> str:
        """
        Static Pose Classifier:
        Compares fingertips (IDs 8, 12, 16, 20) against PIP joints (IDs 6, 10, 14, 18).
        In image space, y=0 is at the top, so:
        - Open Palm: Tip y < PIP y for all 4 fingers
        - Closed Fist: Tip y > PIP y for all 4 fingers
        """
        if not landmarks or len(landmarks) < 21:
            return "UNKNOWN"

        fingers_extended = []
        for tip_id, pip_id in zip(self.FINGERTIP_IDS, self.PIP_IDS):
            # Tip y < PIP y means finger is extended upwards
            is_extended = landmarks[tip_id]["y"] < landmarks[pip_id]["y"]
            fingers_extended.append(is_extended)

        if all(fingers_extended):
            return "OPEN_PALM"
        elif not any(fingers_extended):
            return "CLOSED_FIST"
        else:
            return "UNKNOWN"

    def draw_skeleton(self, frame, hand_landmarks):
        """Draw hand skeleton overlay on frame."""
        self.mp_drawing.draw_landmarks(
            frame,
            hand_landmarks,
            self.mp_hands.HAND_CONNECTIONS,
            self.mp_drawing_styles.get_default_hand_landmarks_style(),
            self.mp_drawing_styles.get_default_hand_connections_style()
        )

    def close(self):
        """Release MediaPipe resources."""
        self.hands.close()
