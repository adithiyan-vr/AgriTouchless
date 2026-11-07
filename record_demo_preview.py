"""
record_demo_preview.py
Generates a 60-second synthetic demonstration video (demo_preview.mp4)
illustrating all 3 core gesture interactions:
1. Closed Fist Dwell (1.0s) -> Digital Scale Tare / Zero
2. Swipe Right & Left -> SOP Recipe Step Navigation
3. Two-Hand 'Hands Up' -> Fail-Safe Emergency Stop Toggle
"""

import os
import cv2
import numpy as np

from hud_controller import HUDController
from produce_detector import ProduceDetector


def create_demo_video(output_filename="demo_preview.mp4", duration_sec=14, fps=30):
    print(f"[DEMO GENERATOR] Generating {duration_sec}s demonstration clip: {output_filename}...")
    width, height = 1280, 720
    total_frames = duration_sec * fps

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_filename, fourcc, fps, (width, height))

    hud = HUDController()
    produce_detector = ProduceDetector(roi_box=(60, 160, 680, 640))
    produce_detector.set_simulated_produce("1")  # Grade-A Tomato on scale

    # Synthetic hand center position
    wrist_x, wrist_y = 450, 420

    for f in range(total_frames):
        # Base canvas: subtle dark ambient greenhouse/kitchen backdrop
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        # Gradient background
        for y in range(height):
            frame[y, :] = (int(30 + 15 * (y / height)), int(40 + 20 * (y / height)), int(25 + 10 * (y / height)))

        # Timeline sequence:
        # 0s - 3s: Tomato on scale, Closed fist dwell -> Tare trigger at 2.2s
        # 3s - 6s: Foreign item placed -> Rejected, Safety Interlock Alert shown
        # 6s - 9s: 500g portion placed -> Farmer Automation Auto-Pack triggers, Crates incremented!
        # 9s - 11.5s: Open Palm Swipe Right & Left navigation
        # 11.5s - 14s: Two-Hand 'Hands Up' -> EMERGENCY STOP toggle

        sec = f / fps
        hands_count = 1
        current_gesture = "OPEN_PALM"
        dwell_progress = 0.0
        dwell_center = (wrist_x, wrist_y)

        if sec < 3.0:
            current_gesture = "CLOSED_FIST" if sec >= 1.0 else "OPEN_PALM"
            is_fist = (sec >= 1.0)
            _draw_synthetic_hand(frame, wrist_x, wrist_y, is_fist=is_fist)
            if is_fist:
                dwell_frac = min(1.0, (sec - 1.0) / 1.0)
                dwell_progress = dwell_frac
                if dwell_frac >= 1.0 and not hud.is_tared:
                    hud.tare_scale()
                cv2.putText(frame, "FEATURE 1: Closed Fist Dwell (1.0s) -> Zero / Tare Scale", (80, 100),
                            cv2.FONT_HERSHEY_DUPLEX, 0.70, (0, 255, 255), 2, cv2.LINE_AA)
            else:
                cv2.putText(frame, "FEATURE 1: Digital Scale - Fresh Harvest Weighed", (80, 100),
                            cv2.FONT_HERSHEY_DUPLEX, 0.70, (255, 255, 255), 2, cv2.LINE_AA)

        elif 3.0 <= sec < 6.0:
            # Place foreign unknown item to demonstrate non-produce rejection
            produce_detector.set_simulated_produce("8")
            current_gesture = "OPEN_PALM"
            _draw_synthetic_hand(frame, wrist_x, wrist_y, is_fist=False)
            cv2.putText(frame, "FEATURE 2: Foreign Object Rejection & Safety Interlock", (80, 100),
                        cv2.FONT_HERSHEY_DUPLEX, 0.70, (40, 140, 255), 2, cv2.LINE_AA)

        elif 6.0 <= sec < 9.0:
            # Place 500g commercial portion to trigger Farmer Automation
            produce_detector.set_simulated_produce("1")
            produce_detector.current_item.base_weight_g = 500.0
            hud.current_step_idx = 2  # Step 3: Weigh 500g
            current_gesture = "OPEN_PALM"
            _draw_synthetic_hand(frame, wrist_x, wrist_y, is_fist=False)
            cv2.putText(frame, "FEATURE 3: Farmer Automation - Auto-Portion & Crate Tally", (80, 100),
                        cv2.FONT_HERSHEY_DUPLEX, 0.70, (0, 255, 120), 2, cv2.LINE_AA)

        elif 9.0 <= sec < 11.5:
            # Dynamic Swipes
            if sec < 10.2:
                swipe_offset = int((sec - 9.0) * 160)
                cur_x = wrist_x + swipe_offset
                current_gesture = "SWIPE_RIGHT"
                _draw_synthetic_hand(frame, cur_x, wrist_y, is_fist=False)
                if sec >= 9.6 and hud.current_step_idx == 3:
                    hud.next_step()
                cv2.putText(frame, "FEATURE 4: Touchless Swipe Right -> Next SOP Step", (80, 100),
                            cv2.FONT_HERSHEY_DUPLEX, 0.70, (100, 255, 100), 2, cv2.LINE_AA)
            else:
                swipe_offset = int((sec - 10.2) * 160)
                cur_x = wrist_x + 120 - swipe_offset
                current_gesture = "SWIPE_LEFT"
                _draw_synthetic_hand(frame, cur_x, wrist_y, is_fist=False)
                if sec >= 10.8 and hud.current_step_idx == 4:
                    hud.prev_step()
                cv2.putText(frame, "FEATURE 4: Touchless Swipe Left -> Previous SOP Step", (80, 100),
                            cv2.FONT_HERSHEY_DUPLEX, 0.70, (100, 255, 255), 2, cv2.LINE_AA)

        else:
            # Two-hand emergency stop
            hands_count = 2
            current_gesture = "EMERGENCY_STOP"
            _draw_synthetic_hand(frame, wrist_x - 120, wrist_y, is_fist=False)
            _draw_synthetic_hand(frame, wrist_x + 120, wrist_y, is_fist=False)

            if not hud.emergency_stop:
                hud.toggle_emergency_stop()

            cv2.putText(frame, "FEATURE 5: Two-Hand 'Hands Up' -> EMERGENCY STOP TRIGGERED", (80, 100),
                        cv2.FONT_HERSHEY_DUPLEX, 0.70, (80, 80, 255), 2, cv2.LINE_AA)

        # Render produce inspection zone
        detected_item = produce_detector.current_item
        produce_detector.draw_inspection_zone(frame, detected_item)

        # Render HUD overlay on top of synthetic frame
        hud.fps = float(fps)
        rendered = hud.render(
            frame,
            hands_detected=hands_count,
            current_gesture=current_gesture,
            dwell_progress=dwell_progress,
            dwell_center=dwell_center,
            detected_produce=detected_item
        )

        out.write(rendered)

    out.release()
    print(f"[DEMO GENERATOR] Video successfully exported to: {output_filename} ({total_frames} frames)")


def _draw_synthetic_hand(frame, wx, wy, is_fist=False):
    """Draws a synthetic hand skeleton visualization for demonstration frames."""
    # Palm base circle
    cv2.circle(frame, (wx, wy), 20, (0, 255, 200), -1, cv2.LINE_AA)
    cv2.circle(frame, (wx, wy), 22, (255, 255, 255), 2, cv2.LINE_AA)

    # 4 Fingers
    offsets = [-35, -12, 12, 35]
    for dx in offsets:
        if is_fist:
            # Curled fingers
            tip_x, tip_y = wx + dx, wy + 15
            pip_x, pip_y = wx + dx, wy - 5
        else:
            # Extended fingers
            tip_x, tip_y = wx + dx, wy - 70
            pip_x, pip_y = wx + dx, wy - 35

        cv2.line(frame, (wx, wy), (pip_x, pip_y), (0, 200, 255), 3, cv2.LINE_AA)
        cv2.line(frame, (pip_x, pip_y), (tip_x, tip_y), (0, 255, 120), 3, cv2.LINE_AA)
        cv2.circle(frame, (pip_x, pip_y), 5, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, (tip_x, tip_y), 6, (0, 150, 255), -1, cv2.LINE_AA)


if __name__ == '__main__':
    create_demo_video()
