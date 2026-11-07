"""
gesture_engine.py
AgriTouchless: Farm & Kitchen Hygiene Controller
Member 1: Computer Vision & Gesture Lead (Adithiyan V R)
"""

import math
import time
from collections import deque
from typing import List, Dict, Tuple, Optional
import cv2
import mediapipe as mp


class GestureEngine:
    """
    Core Computer Vision & Hand Landmark Processing Engine powered by MediaPipe.
    Extracts 21 3D hand landmarks, applies palm-relative distance normalization,
    and classifies static poses (OPEN_PALM vs. CLOSED_FIST), dynamic swipes (SWIPE_LEFT, SWIPE_RIGHT),
    and two-hand fail-safe emergency stop.
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
        Initialize the MediaPipe Hands pipeline, 5-frame rolling buffer, and cooldown timers.
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

        # 5-Frame Rolling Buffer for Wrist Velocity (dx/dt)
        self.wrist_history = deque(maxlen=5)

        # Swipe parameters & debouncing
        self.swipe_threshold = 0.75  # Normalized horizontal velocity threshold (screen width/sec)
        self.swipe_cooldown = 0.8    # 0.8s cooldown to prevent bounce-back accidental swipes
        self.last_swipe_time = 0.0

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

    def update_wrist_trajectory(self, wrist_landmark: Dict[str, float], d_palm: float = 1.0) -> None:
        """
        Record wrist horizontal coordinate and timestamp into the 5-frame rolling buffer.
        """
        now = time.time()
        self.wrist_history.append({
            "time": now,
            "x": wrist_landmark["x"],
            "px": wrist_landmark["px"],
            "d_palm": max(1e-5, d_palm)
        })

    def detect_swipe(self, pose: str) -> Optional[str]:
        """
        Dynamic Swipe Recognition:
        Computes wrist horizontal velocity (dx/dt) over the 5-frame rolling buffer.
        Requirements:
        - Hand must be in 'OPEN_PALM' pose
        - 0.8s cooldown elapsed to prevent accidental reverse swipes
        Returns:
        - 'SWIPE_RIGHT': next SOP/recipe step
        - 'SWIPE_LEFT': previous SOP/recipe step
        - None: no swipe detected or threshold not met
        """
        now = time.time()
        if now - self.last_swipe_time < self.swipe_cooldown:
            return None

        # Swipe requires intentional open palm motion
        if pose != "OPEN_PALM":
            return None

        if len(self.wrist_history) < 5:
            return None

        t_start = self.wrist_history[0]["time"]
        t_end = self.wrist_history[-1]["time"]
        dt = t_end - t_start

        if dt <= 0.001 or dt > 0.4:
            # Buffer too stale or time window invalid
            return None

        x_start = self.wrist_history[0]["x"]
        x_end = self.wrist_history[-1]["x"]
        dx = x_end - x_start

        # Calculate horizontal velocity vx = dx / dt
        # In mirrored frame, positive dx indicates motion toward the user's right
        vx = dx / dt

        if vx > self.swipe_threshold:
            self.last_swipe_time = now
            self.wrist_history.clear()
            return "SWIPE_RIGHT"
        elif vx < -self.swipe_threshold:
            self.last_swipe_time = now
            self.wrist_history.clear()
            return "SWIPE_LEFT"

        return None

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
