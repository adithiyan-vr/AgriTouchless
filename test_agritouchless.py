"""
test_agritouchless.py
Unit and Integration Tests for AgriTouchless: Farm & Kitchen Hygiene Controller
Validates Gesture Engine, Produce Detector, and HUD & State Controller components.
"""

import math
import sys
import time
import unittest
import numpy as np

from gesture_engine import GestureEngine
from hud_controller import HUDController
from produce_detector import ProduceDetector, ProduceItem


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
        Verify rotation-invariant static pose classifier:
        - OPEN_PALM: Fingers extended outward away from wrist/MCPs
        - CLOSED_FIST: Fingers curled tightly into palm
        """
        engine = GestureEngine()

        # Build Open Palm mock (fingertips extended far from wrist at 0.5, 0.8)
        open_palm_lms = [{"id": i, "x": 0.5, "y": 0.5, "z": 0.0, "px": 640, "py": 360} for i in range(21)]
        open_palm_lms[engine.WRIST] = {"id": 0, "x": 0.5, "y": 0.8, "z": 0.0, "px": 640, "py": 576}
        open_palm_lms[engine.MIDDLE_MCP] = {"id": 9, "x": 0.5, "y": 0.5, "z": 0.0, "px": 640, "py": 360}
        for pip_id, tip_id in zip(engine.PIP_IDS, engine.FINGERTIP_IDS):
            open_palm_lms[pip_id]["y"] = 0.4
            open_palm_lms[tip_id]["y"] = 0.15

        self.assertEqual(engine.classify_hand_pose(open_palm_lms), "OPEN_PALM")

        # Build Closed Fist mock (fingertips curled close to wrist and below PIPs)
        closed_fist_lms = [{"id": i, "x": 0.5, "y": 0.5, "z": 0.0, "px": 640, "py": 360} for i in range(21)]
        closed_fist_lms[engine.WRIST] = {"id": 0, "x": 0.5, "y": 0.8, "z": 0.0, "px": 640, "py": 576}
        closed_fist_lms[engine.MIDDLE_MCP] = {"id": 9, "x": 0.5, "y": 0.6, "z": 0.0, "px": 640, "py": 432}
        for pip_id, tip_id in zip(engine.PIP_IDS, engine.FINGERTIP_IDS):
            closed_fist_lms[pip_id]["y"] = 0.55
            closed_fist_lms[tip_id]["y"] = 0.68

        self.assertEqual(engine.classify_hand_pose(closed_fist_lms), "CLOSED_FIST")

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

    def test_produce_detector_and_scale_integration(self):
        """
        Verify Fruit & Vegetable identification and dynamic load-cell scale weighing.
        """
        detector = ProduceDetector()
        hud = HUDController()

        # Simulate Tomato placement
        detector.set_simulated_produce("1")
        item = detector.current_item
        self.assertIsNotNone(item)
        self.assertIn("Tomato", item.name)
        self.assertGreater(item.base_weight_g, 100.0)

        # Scale responds to placed tomato
        for _ in range(5):
            hud.update_simulation(detected_produce=item)

        self.assertGreater(hud.net_weight, 50.0)
        self.assertIn("Tomato", hud.detected_produce_name)

        # Tare the scale with tomato on it
        hud.tare_scale()
        self.assertAlmostEqual(hud.net_weight, 0.0, places=1)
        self.assertTrue(hud.is_tared)

        # Clear produce (empty scale platter) -> scale shows negative tare offset
        detector.set_simulated_produce("0")
        for _ in range(5):
            hud.update_simulation(detected_produce=None)

        self.assertLess(hud.net_weight, -50.0)  # Real digital scale negative offset
        self.assertEqual(hud.detected_produce_name, "EMPTY PLATTER")

        # SOP Navigation
        hud.next_step()
        self.assertEqual(hud.current_step_idx, 2)
        hud.prev_step()
        self.assertEqual(hud.current_step_idx, 1)

        # Emergency Stop
        hud.toggle_emergency_stop()
        self.assertTrue(hud.emergency_stop)

        # Render complete HUD frame
        blank_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        rendered = hud.render(blank_frame, hands_detected=1, current_gesture="OPEN_PALM",
                              dwell_progress=0.5, dwell_center=(400, 300), detected_produce=item)
        self.assertEqual(rendered.shape, (720, 1280, 3))


if __name__ == '__main__':
    unittest.main()
