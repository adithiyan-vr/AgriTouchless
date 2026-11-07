"""
test_agritouchless.py
Unit and Integration Tests for AgriTouchless: Farm & Kitchen Hygiene Controller
Validates Member 1 (Gesture Engine) and Member 2 (HUD & State Controller) components.
"""

import time
import math
import numpy as np
import sys
import unittest
from gesture_engine import GestureEngine
from hud_controller import HUDController


class TestAgriTouchless(unittest.TestCase):

    def test_gesture_engine_init(self):
        """Verify GestureEngine initializes cleanly."""
        engine = GestureEngine(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.5)
        self.assertEqual(engine.wrist_history.maxlen, 5)
        self.assertGreater(engine.swipe_threshold, 0.0)
        self.assertEqual(engine.swipe_cooldown, 0.8)
        self.assertEqual(engine.fist_dwell_max, 30)
        engine.close()

    def test_normalization_algorithm(self):
        """
        Verify distance-independent normalization:
        Coordinates normalized relative to Wrist (ID 0) and scaled by d_palm = sqrt((x9-x0)^2 + (y9-y0)^2).
        """
        engine = GestureEngine()

        landmarks = []
        for i in range(21):
            landmarks.append({
                "id": i,
                "x": 0.5 + i * 0.01,
                "y": 0.5 + i * 0.01,
                "z": 0.0,
                "px": 640 + i * 10,
                "py": 360 + i * 10
            })

        normalized = engine.normalize_landmarks(landmarks)
        self.assertEqual(len(normalized), 21)
        self.assertAlmostEqual(normalized[0]["norm_x"], 0.0, places=5)
        self.assertAlmostEqual(normalized[0]["norm_y"], 0.0, places=5)

        mcp_dist = math.sqrt(normalized[9]["norm_x"]**2 + normalized[9]["norm_y"]**2)
        self.assertAlmostEqual(mcp_dist, 1.0, places=4)

        engine.close()

    def test_static_pose_classification(self):
        """
        Verify static pose classifier:
        - OPEN_PALM: Tip y < PIP y for all 4 fingers (extended upwards)
        - CLOSED_FIST: Tip y > PIP y for all 4 fingers (curled into palm)
        """
        engine = GestureEngine()

        open_palm_lms = [{"id": i, "x": 0.5, "y": 0.5, "z": 0.0, "px": 640, "py": 360} for i in range(21)]
        for pip_id, tip_id in zip(engine.PIP_IDS, engine.FINGERTIP_IDS):
            open_palm_lms[pip_id]["y"] = 0.4
            open_palm_lms[tip_id]["y"] = 0.2

        self.assertEqual(engine.classify_hand_pose(open_palm_lms), "OPEN_PALM")

        closed_fist_lms = [{"id": i, "x": 0.5, "y": 0.5, "z": 0.0, "px": 640, "py": 360} for i in range(21)]
        for pip_id, tip_id in zip(engine.PIP_IDS, engine.FINGERTIP_IDS):
            closed_fist_lms[pip_id]["y"] = 0.4
            closed_fist_lms[tip_id]["y"] = 0.6

        self.assertEqual(engine.classify_hand_pose(closed_fist_lms), "CLOSED_FIST")

        ambiguous_lms = [{"id": i, "x": 0.5, "y": 0.5, "z": 0.0, "px": 640, "py": 360} for i in range(21)]
        ambiguous_lms[engine.INDEX_PIP]["y"] = 0.4
        ambiguous_lms[engine.INDEX_TIP]["y"] = 0.2
        ambiguous_lms[engine.PINKY_PIP]["y"] = 0.4
        ambiguous_lms[engine.PINKY_TIP]["y"] = 0.6

        self.assertEqual(engine.classify_hand_pose(ambiguous_lms), "UNKNOWN")

        engine.close()

    def test_swipe_velocity_detection(self):
        """
        Verify 5-frame buffer and horizontal velocity calculation for SWIPE_RIGHT and SWIPE_LEFT.
        """
        engine = GestureEngine()
        base_time = time.time()

        for i in range(5):
            engine.wrist_history.append({
                "time": base_time + i * 0.04,
                "x": 0.2 + i * 0.08,
                "px": 200 + i * 80,
                "d_palm": 0.15
            })

        swipe = engine.detect_swipe("OPEN_PALM")
        self.assertEqual(swipe, "SWIPE_RIGHT")
        self.assertEqual(len(engine.wrist_history), 0)

        # Immediate repeat should be suppressed by cooldown
        for i in range(5):
            engine.wrist_history.append({
                "time": base_time + 0.25 + i * 0.04,
                "x": 0.2 + i * 0.08,
                "px": 200 + i * 80,
                "d_palm": 0.15
            })
        self.assertIsNone(engine.detect_swipe("OPEN_PALM"))

        # Left swipe
        engine.last_swipe_time = base_time - 2.0
        engine.wrist_history.clear()
        for i in range(5):
            engine.wrist_history.append({
                "time": base_time + i * 0.04,
                "x": 0.7 - i * 0.08,
                "px": 700 - i * 80,
                "d_palm": 0.15
            })

        swipe_left = engine.detect_swipe("OPEN_PALM")
        self.assertEqual(swipe_left, "SWIPE_LEFT")

        # Closed fist should not trigger swipe
        engine.last_swipe_time = base_time - 2.0
        for i in range(5):
            engine.wrist_history.append({
                "time": base_time + i * 0.04,
                "x": 0.2 + i * 0.08,
                "px": 200 + i * 80,
                "d_palm": 0.15
            })
        self.assertIsNone(engine.detect_swipe("CLOSED_FIST"))

        engine.close()

    def test_two_hand_emergency_stop(self):
        """
        Verify two-hand 'Hands Up' emergency stop detector.
        """
        engine = GestureEngine()
        engine.two_hand_threshold = 3

        self.assertFalse(engine.detect_two_hand_stop(["OPEN_PALM"]))
        self.assertFalse(engine.detect_two_hand_stop(["OPEN_PALM", "CLOSED_FIST"]))

        engine.detect_two_hand_stop(["OPEN_PALM", "OPEN_PALM"])
        engine.detect_two_hand_stop(["OPEN_PALM", "OPEN_PALM"])
        triggered = engine.detect_two_hand_stop(["OPEN_PALM", "OPEN_PALM"])
        self.assertTrue(triggered)

        engine.close()

    def test_hud_controller_state_and_render(self):
        """
        Verify HUD Controller state machine & OpenCV render.
        """
        hud = HUDController()
        self.assertFalse(hud.emergency_stop)
        self.assertEqual(hud.current_step_idx, 1)
        self.assertGreater(hud.net_weight, 0)

        hud.tare_scale()
        self.assertAlmostEqual(hud.net_weight, 0.0, places=3)

        hud.next_step()
        self.assertEqual(hud.current_step_idx, 2)
        hud.prev_step()
        self.assertEqual(hud.current_step_idx, 1)

        hud.toggle_emergency_stop()
        self.assertTrue(hud.emergency_stop)

        blank_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        rendered = hud.render(blank_frame, hands_detected=1, current_gesture="OPEN_PALM",
                              dwell_progress=0.5, dwell_center=(400, 300))
        self.assertEqual(rendered.shape, (720, 1280, 3))


if __name__ == '__main__':
    unittest.main()

