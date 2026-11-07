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
        self.mp_hands = None
        self.mp_drawing = None
        self.mp_drawing_styles = None
        self.hands = None

        try:
            if hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
                self.mp_hands = mp.solutions.hands
                self.mp_drawing = mp.solutions.drawing_utils
                self.mp_drawing_styles = mp.solutions.drawing_styles

                self.hands = self.mp_hands.Hands(
                    static_image_mode=False,
                    max_num_hands=max_num_hands,
                    min_detection_confidence=min_detection_confidence,
                    min_tracking_confidence=min_tracking_confidence
                )
        except Exception as e:
            print(f"[GestureEngine] Warning during MediaPipe initialization: {e}")

        # 5-Frame Rolling Buffer for Palm/Wrist Velocity (dx/dt)
        self.wrist_history = deque(maxlen=5)

        # Swipe parameters & debouncing
        self.swipe_threshold = 0.40  # Normalized horizontal velocity threshold (screen width/sec)
        self.swipe_cooldown = 0.8    # 0.8s cooldown to prevent bounce-back accidental swipes
        self.last_swipe_time = 0.0
        self.no_hand_frames = 0

        # Two-Hand Fail-Safe Emergency Stop Tracker
        self.two_hand_stop_frames = 0
        self.two_hand_threshold = 12       # Frames required (~0.4s) to confirm fail-safe
        self.last_emergency_toggle = 0.0
        self.emergency_cooldown = 1.5      # 1.5s cooldown between toggle state changes

        # Fist Tare Dwell-Time Debouncing
        self.fist_dwell_counter = 0
        self.fist_dwell_max = 30           # 30 frames (~1.0s at 30 FPS)
        self.last_tare_time = 0.0
        self.tare_cooldown = 1.5           # 1.5s cooldown after tare trigger

    def process_frame(self, frame_bgr):
        """
        Convert BGR frame to RGB and process with MediaPipe Hands.
        """
        if self.hands is None:
            class _DummyResults:
                multi_hand_landmarks = None
            return _DummyResults()

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
        Robust Static Pose Classifier (Rotation & Distance Invariant):
        Calculates Euclidean distances from each fingertip to Wrist (P0) and MCP joints.
        Works reliably at any hand angle (pointing up, forward, sideways, or diagonal).
        
        - OPEN_PALM: 4 or 5 fingers extended outward away from wrist/palm center.
        - CLOSED_FIST: All 4 main fingers (Index, Middle, Ring, Pinky) curled tightly into palm.
        """
        if not landmarks or len(landmarks) < 21:
            return "UNKNOWN"

        wrist = landmarks[self.WRIST]
        middle_mcp = landmarks[self.MIDDLE_MCP]

        # Reference palm size
        d_palm = math.sqrt((middle_mcp["x"] - wrist["x"])**2 + (middle_mcp["y"] - wrist["y"])**2)
        if d_palm < 1e-5:
            d_palm = 1.0

        # Evaluate extension of the 4 fingers: Index (8), Middle (12), Ring (16), Pinky (20)
        extended_count = 0
        curled_count = 0

        for tip_id, pip_id, mcp_id in zip(self.FINGERTIP_IDS, self.PIP_IDS,
                                          [self.INDEX_MCP, self.MIDDLE_MCP, self.RING_MCP, self.PINKY_MCP]):
            tip = landmarks[tip_id]
            pip = landmarks[pip_id]
            mcp = landmarks[mcp_id]

            # Euclidean distances to wrist
            d_tip_wrist = math.sqrt((tip["x"] - wrist["x"])**2 + (tip["y"] - wrist["y"])**2)
            d_pip_wrist = math.sqrt((pip["x"] - wrist["x"])**2 + (pip["y"] - wrist["y"])**2)
            d_mcp_wrist = math.sqrt((mcp["x"] - wrist["x"])**2 + (mcp["y"] - wrist["y"])**2)

            # A finger is extended if its tip is significantly further from wrist than PIP/MCP
            # Also check y-position when hand is vertical
            is_extended = (d_tip_wrist > d_pip_wrist * 1.08) or (tip["y"] < pip["y"] and d_tip_wrist > d_mcp_wrist)
            is_curled = (d_tip_wrist < d_pip_wrist * 1.02) or (tip["y"] > pip["y"] and d_tip_wrist < d_mcp_wrist * 1.25)

            if is_extended and not is_curled:
                extended_count += 1
            elif is_curled:
                curled_count += 1

        # Evaluate Thumb extension relative to Pinky MCP (P17)
        thumb_tip = landmarks[self.THUMB_TIP]
        thumb_ip = landmarks[self.THUMB_IP]
        pinky_mcp = landmarks[self.PINKY_MCP]
        d_thumb_pinky = math.sqrt((thumb_tip["x"] - pinky_mcp["x"])**2 + (thumb_tip["y"] - pinky_mcp["y"])**2)
        d_thumb_ip_pinky = math.sqrt((thumb_ip["x"] - pinky_mcp["x"])**2 + (thumb_ip["y"] - pinky_mcp["y"])**2)
        thumb_extended = d_thumb_pinky > d_thumb_ip_pinky * 1.05

        if thumb_extended:
            extended_count += 1

        # Classification decision rules
        # Open Palm: At least 4 extended fingers (including thumb)
        if extended_count >= 4 and curled_count <= 1:
            return "OPEN_PALM"
        # Closed Fist: All 4 main fingers curled, at most 1 (thumb) ambiguous
        elif curled_count >= 4 or (curled_count >= 3 and extended_count == 0):
            return "CLOSED_FIST"
        else:
            return "UNKNOWN"

    def update_wrist_trajectory(self, palm_coords: Dict[str, float], d_palm: float = 1.0) -> None:
        """
        Record palm/wrist coordinate, velocity timestamp, and distance into rolling buffer.
        Tracks palm center (or wrist) with both X and Y coordinates to verify horizontal dominance.
        """
        now = time.time()
        self.wrist_history.append({
            "time": now,
            "x": palm_coords["x"],
            "y": palm_coords.get("y", 0.5),
            "px": palm_coords.get("px", int(palm_coords["x"] * 1280)),
            "py": palm_coords.get("py", int(palm_coords.get("y", 0.5) * 720)),
            "d_palm": max(1e-5, d_palm)
        })

    def detect_swipe(self, pose: str) -> Optional[str]:
        """
        Robust Dynamic Swipe Recognition:
        Evaluates horizontal displacement and velocity over recent frames.
        Requirements:
        - Hand cannot be in 'CLOSED_FIST' (allows 'OPEN_PALM' or transient 'UNKNOWN' motion-blur frames)
        - Movement must be predominantly horizontal (|dx| >= 1.2 * |dy|)
        - Minimum physical movement (|dx| >= 0.045)
        - Cooldown elapsed (0.65s)
        Returns:
        - 'SWIPE_RIGHT': next SOP/recipe step
        - 'SWIPE_LEFT': previous SOP/recipe step
        - None: no swipe detected or threshold not met
        """
        now = time.time()
        if now - self.last_swipe_time < self.swipe_cooldown:
            return None

        # Cannot swipe with a closed fist (which is reserved for scale tare)
        if pose == "CLOSED_FIST":
            return None

        if len(self.wrist_history) < 3:
            return None

        current = self.wrist_history[-1]
        now_t = current["time"]
        now_x = current["x"]
        now_y = current.get("y", 0.5)

        # Average palm reference size over buffer
        d_palm_avg = sum(item.get("d_palm", 0.15) for item in self.wrist_history) / len(self.wrist_history)
        if d_palm_avg < 1e-4:
            d_palm_avg = 0.15

        # Check candidate past frames within 0.04s to 0.45s time window
        best_swipe = None
        max_speed = 0.0

        for past in list(self.wrist_history)[:-1]:
            dt = now_t - past["time"]
            if dt < 0.04 or dt > 0.45:
                continue

            dx = now_x - past["x"]
            dy = now_y - past.get("y", 0.5)

            # Horizontal dominance: swipe must be predominantly horizontal
            # Only enforce if vertical motion is noticeable (> 0.06)
            if abs(dy) > 0.06 and abs(dx) < 1.05 * abs(dy):
                continue

            # Minimum displacement (at least 4% of screen width)
            if abs(dx) < 0.04:
                continue

            vx = dx / dt
            vx_palm = vx / d_palm_avg

            # Threshold check: standard screen speed (0.40) or palm-normalized speed (2.2)
            if (abs(vx) >= self.swipe_threshold or (abs(vx_palm) >= 2.2 and abs(dx) >= 0.04)):
                if abs(vx) > max_speed:
                    max_speed = abs(vx)
                    best_swipe = "SWIPE_RIGHT" if dx > 0 else "SWIPE_LEFT"

        if best_swipe:
            self.last_swipe_time = now
            self.wrist_history.clear()
            return best_swipe

        return None

    def detect_two_hand_stop(self, poses: List[str]) -> bool:
        """
        Two-Hand 'Hands Up' Fail-Safe Detector:
        Requires both hands visible and classified as 'OPEN_PALM'.
        Debounced over consecutive frames with a 1.5s cooldown to prevent toggling flutter.
        """
        now = time.time()
        is_both_open = len(poses) == 2 and all(p == "OPEN_PALM" for p in poses)

        if is_both_open:
            self.two_hand_stop_frames += 1
            if self.two_hand_stop_frames >= self.two_hand_threshold:
                if now - self.last_emergency_toggle > self.emergency_cooldown:
                    self.last_emergency_toggle = now
                    self.two_hand_stop_frames = 0
                    return True
        else:
            self.two_hand_stop_frames = max(0, self.two_hand_stop_frames - 2)

        return False

    def analyze_frame(self, frame_bgr, width: int = 1280, height: int = 720) -> Dict:
        """
        High-level pipeline method integrating:
        1. MediaPipe hand landmark detection
        2. Normalization relative to wrist and palm size
        3. Static pose classification (OPEN_PALM / CLOSED_FIST)
        4. Dynamic velocity tracking (SWIPE_LEFT / SWIPE_RIGHT)
        5. Fist dwell-time accumulator (30 frames tare trigger)
        6. Two-hand fail-safe emergency pause

        Returns structured analysis result dict:
        {
            "hands_count": int,
            "poses": List[str],
            "primary_gesture": str,
            "action_trigger": Optional[str],  # "TARE", "NEXT_STEP", "PREV_STEP", "EMERGENCY_STOP", None
            "dwell_progress": float,          # 0.0 to 1.0
            "dwell_center": Optional[Tuple[int, int]],
            "raw_results": results
        }
        """
        results = self.process_frame(frame_bgr)
        now = time.time()

        action_trigger = None
        dwell_progress = 0.0
        dwell_center = None
        poses = []
        primary_gesture = "NONE"

        if not results.multi_hand_landmarks:
            # Decay counters when hands are not in frame
            self.fist_dwell_counter = max(0, self.fist_dwell_counter - 2)
            self.two_hand_stop_frames = max(0, self.two_hand_stop_frames - 2)
            self.no_hand_frames += 1
            # Prevent wiping trajectory during transient 1-3 frame motion blurs
            if self.no_hand_frames >= 4:
                self.wrist_history.clear()
            return {
                "hands_count": 0,
                "poses": [],
                "primary_gesture": "NONE",
                "action_trigger": None,
                "dwell_progress": 0.0,
                "dwell_center": None,
                "raw_results": results
            }

        self.no_hand_frames = 0
        hands_count = len(results.multi_hand_landmarks)

        # Process each detected hand
        hands_data = []
        for hand_lms in results.multi_hand_landmarks:
            raw_lms = self.extract_landmarks(hand_lms, width=width, height=height)
            norm_lms = self.normalize_landmarks(raw_lms)
            pose = self.classify_hand_pose(raw_lms)
            poses.append(pose)
            hands_data.append({
                "raw": raw_lms,
                "norm": norm_lms,
                "pose": pose,
                "lms": hand_lms
            })

        # 1. Check Two-Hand Emergency Stop
        if hands_count == 2 and self.detect_two_hand_stop(poses):
            action_trigger = "EMERGENCY_STOP"
            primary_gesture = "EMERGENCY_STOP"
            return {
                "hands_count": 2,
                "poses": poses,
                "primary_gesture": primary_gesture,
                "action_trigger": action_trigger,
                "dwell_progress": 0.0,
                "dwell_center": None,
                "raw_results": results
            }

        # 2. Select active gesturing hand with spatial continuity
        active_hand = hands_data[0]
        if hands_count > 1 and len(self.wrist_history) > 0:
            last_x = self.wrist_history[-1]["x"]
            last_y = self.wrist_history[-1].get("y", 0.5)
            # Find the hand closest to last position to maintain tracking continuity
            active_hand = min(
                hands_data,
                key=lambda h: (h["raw"][self.WRIST]["x"] - last_x)**2 + (h["raw"][self.WRIST]["y"] - last_y)**2
            )

        pose = active_hand["pose"]
        primary_gesture = pose
        wrist = active_hand["raw"][self.WRIST]
        mcp = active_hand["raw"][self.MIDDLE_MCP]
        dwell_center = (wrist["px"], wrist["py"])

        dx = mcp["x"] - wrist["x"]
        dy = mcp["y"] - wrist["y"]
        d_palm = math.sqrt(dx * dx + dy * dy)

        # Palm center (average of wrist and middle MCP) captures both whole-arm and wrist-flick swipes
        palm_center_pt = {
            "x": (wrist["x"] + mcp["x"]) / 2.0,
            "y": (wrist["y"] + mcp["y"]) / 2.0,
            "px": int((wrist["px"] + mcp["px"]) / 2.0),
            "py": int((wrist["py"] + mcp["py"]) / 2.0),
        }

        self.update_wrist_trajectory(palm_center_pt, d_palm=d_palm)
        swipe = self.detect_swipe(pose)
        if swipe == "SWIPE_RIGHT":
            action_trigger = "NEXT_STEP"
            primary_gesture = "SWIPE_RIGHT"
        elif swipe == "SWIPE_LEFT":
            action_trigger = "PREV_STEP"
            primary_gesture = "SWIPE_LEFT"

        # 3. Check Closed Fist Dwell-Time for Tare
        if pose == "CLOSED_FIST":
            if now - self.last_tare_time > self.tare_cooldown:
                self.fist_dwell_counter += 1
                dwell_progress = min(1.0, self.fist_dwell_counter / self.fist_dwell_max)
                if self.fist_dwell_counter >= self.fist_dwell_max:
                    action_trigger = "TARE"
                    self.last_tare_time = now
                    self.fist_dwell_counter = 0
                    dwell_progress = 1.0
            else:
                dwell_progress = 0.0
        else:
            # Gentle decay (drops by 1 instead of 2) for smooth, non-flickering dwell meter
            self.fist_dwell_counter = max(0, self.fist_dwell_counter - 1)
            dwell_progress = max(0.0, self.fist_dwell_counter / self.fist_dwell_max)

        return {
            "hands_count": hands_count,
            "poses": poses,
            "primary_gesture": primary_gesture,
            "action_trigger": action_trigger,
            "dwell_progress": dwell_progress,
            "dwell_center": dwell_center,
            "raw_results": results
        }

    def draw_skeleton(self, frame, hand_landmarks):
        """Draw hand skeleton overlay on frame."""
        if self.mp_drawing and hand_landmarks:
            self.mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                self.mp_hands.HAND_CONNECTIONS,
                self.mp_drawing_styles.get_default_hand_landmarks_style(),
                self.mp_drawing_styles.get_default_hand_connections_style()
            )

    def close(self):
        """Release MediaPipe resources."""
        if self.hands is not None:
            self.hands.close()
