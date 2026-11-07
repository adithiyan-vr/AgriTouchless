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


def create_demo_video(output_filename="demo_preview.mp4", duration_sec=10, fps=30):
    print(f"[DEMO GENERATOR] Generating {duration_sec}s demonstration clip: {output_filename}...")
    width, height = 1280, 720
    total_frames = duration_sec * fps

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_filename, fourcc, fps, (width, height))

    hud = HUDController()
    hud.raw_weight = 1250.0

    # Synthetic hand center position
    wrist_x, wrist_y = 450, 420

    for f in range(total_frames):
        # Base canvas: subtle dark ambient greenhouse/kitchen backdrop
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        # Gradient background
        for y in range(height):
            frame[y, :] = (int(30 + 15 * (y / height)), int(40 + 20 * (y / height)), int(25 + 10 * (y / height)))

        # Timeline sequence:
        # 0s - 2s: Idle tracking (Open Palm)
        # 2s - 4s: Closed fist dwell -> Tare trigger at 3.5s
        # 4s - 6s: Swipe Right -> SOP Step 2 -> Step 3
        # 6s - 7.5s: Swipe Left -> SOP Step 3 -> Step 2
        # 7.5s - 10s: Two hands up -> EMERGENCY STOP toggle

        sec = f / fps
        hands_count = 1
        current_gesture = "OPEN_PALM"
        dwell_progress = 0.0
        dwell_center = (wrist_x, wrist_y)

        # Draw a synthetic stylized hand skeleton representation
        if sec < 2.0:
            current_gesture = "OPEN_PALM"
            _draw_synthetic_hand(frame, wrist_x, wrist_y, is_fist=False)
            cv2.putText(frame, "DEMO: Worker sorting produce - Open Palm (Ready)", (80, 100),
                        cv2.FONT_HERSHEY_DUPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)

        elif 2.0 <= sec < 4.0:
            current_gesture = "CLOSED_FIST"
            dwell_frac = min(1.0, (sec - 2.0) / 1.0)  # 1.0s dwell
            dwell_progress = dwell_frac
            _draw_synthetic_hand(frame, wrist_x, wrist_y, is_fist=True)

            if dwell_frac >= 1.0 and hud.net_weight > 0:
                hud.tare_scale()

            cv2.putText(frame, "DEMO: Closed Fist Dwell (1.0s) -> Scale Tared to 0.0g", (80, 100),
                        cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 255, 255), 2, cv2.LINE_AA)

        elif 4.0 <= sec < 6.0:
            # Swipe right motion
            swipe_offset = int((sec - 4.0) * 200)
            cur_x = wrist_x + swipe_offset
            current_gesture = "SWIPE_RIGHT"
            _draw_synthetic_hand(frame, cur_x, wrist_y, is_fist=False)

            if sec >= 4.6 and hud.current_step_idx == 1:
                hud.next_step()

            cv2.putText(frame, "DEMO: Swipe Right -> Advance to Next SOP Step", (80, 100),
                        cv2.FONT_HERSHEY_DUPLEX, 0.75, (100, 255, 100), 2, cv2.LINE_AA)

        elif 6.0 <= sec < 7.5:
            # Swipe left motion
            swipe_offset = int((sec - 6.0) * 180)
            cur_x = wrist_x + 150 - swipe_offset
            current_gesture = "SWIPE_LEFT"
            _draw_synthetic_hand(frame, cur_x, wrist_y, is_fist=False)

            if sec >= 6.6 and hud.current_step_idx == 2:
                hud.prev_step()

            cv2.putText(frame, "DEMO: Swipe Left -> Return to Previous SOP Step", (80, 100),
                        cv2.FONT_HERSHEY_DUPLEX, 0.75, (100, 255, 255), 2, cv2.LINE_AA)

        else:
            # Two-hand emergency stop
            hands_count = 2
            current_gesture = "EMERGENCY_STOP"
            _draw_synthetic_hand(frame, wrist_x - 120, wrist_y, is_fist=False)
            _draw_synthetic_hand(frame, wrist_x + 120, wrist_y, is_fist=False)

            if not hud.emergency_stop:
                hud.toggle_emergency_stop()

            cv2.putText(frame, "DEMO: Two-Hand 'Hands Up' -> EMERGENCY STOP TRIGGERED", (80, 100),
                        cv2.FONT_HERSHEY_DUPLEX, 0.75, (80, 80, 255), 2, cv2.LINE_AA)

        # Render HUD overlay on top of synthetic frame
        hud.fps = float(fps)
        rendered = hud.render(
            frame,
            hands_detected=hands_count,
            current_gesture=current_gesture,
            dwell_progress=dwell_progress,
            dwell_center=dwell_center
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
