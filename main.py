"""
main.py
AgriTouchless: Farm & Kitchen Hygiene Controller
TinkerHub Saturday Hack Night (Season 02: AgriTech & Food)
Integrated by Member 1 (Adithiyan V R) & Member 2 (Jazeem Anwar)
"""

import os
import sys
import time
import cv2
import numpy as np

from gesture_engine import GestureEngine
from hud_controller import HUDController


def run_controller():
    print("=" * 65)
    print("  AgriTouchless: Farm & Kitchen Hygiene Controller")
    print("  TinkerHub Saturday Hack Night | Season 02: AgriTech & Food")
    print("=" * 65)
    print("Initializing Computer Vision Gesture Engine & HUD Controller...")

    # Initialize Gesture Engine and HUD Controller
    engine = GestureEngine(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.5)
    hud = HUDController()

    target_width, target_height = 1280, 720

    # Initialize Webcam
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, target_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, target_height)

    camera_available = cap.isOpened()
    if not camera_available:
        print("[WARNING] Live webcam (Index 0) not detected!")
        print("[INFO] Starting in Demo Synthetic Mode for verification...")
        cap.release()

    prev_time = time.time()
    fps_smooth = 30.0

    window_name = "AgriTouchless - Farm & Kitchen Hygiene Controller"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, target_width, target_height)

    print("\nSystem Controls & Gesture Guide:")
    print("  • Closed Fist (Hold 1.0s) : TARE / Zero Digital Scale")
    print("  • Swipe Left / Right      : Previous / Next SOP Recipe Step")
    print("  • Two-Hand 'Hands Up'     : Toggle EMERGENCY STOP / Machinery Pause")
    print("  • Keyboard shortcuts      : 't' (Tare), 'n' (Next), 'p' (Prev), 'e' (E-Stop), 'q'/ESC (Quit)\n")

    try:
        frame_idx = 0
        while True:
            start_frame = time.time()

            if camera_available:
                ret, frame = cap.read()
                if not ret:
                    print("[INFO] Camera frame read failed. Re-trying...")
                    time.sleep(0.05)
                    continue
            else:
                # Generate synthetic test frame if no hardware webcam connected
                frame = np.zeros((target_height, target_width, 3), dtype=np.uint8)
                # Dark farm greenhouse backdrop simulation
                frame[:] = (35, 45, 30)
                cv2.putText(frame, "SYNTHETIC DEMO STREAM (Camera 0 not connected)",
                            (target_width // 2 - 280, target_height // 2),
                            cv2.FONT_HERSHEY_DUPLEX, 0.7, (180, 180, 180), 1, cv2.LINE_AA)
                cv2.putText(frame, "Use Keys: 't'=Tare | 'n'=Next Step | 'p'=Prev Step | 'e'=E-Stop | 'q'=Quit",
                            (target_width // 2 - 380, target_height // 2 + 45),
                            cv2.FONT_HERSHEY_DUPLEX, 0.65, (0, 200, 255), 1, cv2.LINE_AA)

            # Mirror view for natural interaction
            frame = cv2.flip(frame, 1)

            # Ensure strict 1280x720 aspect ratio
            if frame.shape[1] != target_width or frame.shape[0] != target_height:
                frame = cv2.resize(frame, (target_width, target_height))

            # Run Computer Vision analysis
            analysis = engine.analyze_frame(frame, width=target_width, height=target_height)

            hands_count = analysis["hands_count"]
            primary_gesture = analysis["primary_gesture"]
            action = analysis["action_trigger"]
            dwell_progress = analysis["dwell_progress"]
            dwell_center = analysis["dwell_center"]

            # Dispatch Touchless Actions to HUD State Machine
            if action == "TARE":
                print("[GESTURE TRIGGER] Closed Fist Dwell -> Scale TARE / ZEROED")
                hud.tare_scale()
            elif action == "NEXT_STEP":
                print("[GESTURE TRIGGER] Swipe Right -> Advancing to Next SOP Step")
                hud.next_step()
            elif action == "PREV_STEP":
                print("[GESTURE TRIGGER] Swipe Left -> Returning to Previous SOP Step")
                hud.prev_step()
            elif action == "EMERGENCY_STOP":
                print("[GESTURE TRIGGER] Two-Hand Hands Up -> Toggling EMERGENCY STOP")
                hud.toggle_emergency_stop()

            # Draw MediaPipe hand landmarks skeleton
            if analysis["raw_results"].multi_hand_landmarks:
                for hand_lms in analysis["raw_results"].multi_hand_landmarks:
                    engine.draw_skeleton(frame, hand_lms)

            # Calculate FPS
            curr_time = time.time()
            dt = curr_time - prev_time
            prev_time = curr_time
            if dt > 0:
                current_fps = 1.0 / dt
                fps_smooth = 0.9 * fps_smooth + 0.1 * current_fps
            hud.fps = fps_smooth

            # Render complete OpenCV HUD overlay
            display_frame = hud.render(
                frame,
                hands_detected=hands_count,
                current_gesture=primary_gesture,
                dwell_progress=dwell_progress,
                dwell_center=dwell_center
            )

            cv2.imshow(window_name, display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord('q'):
                print("[INFO] Exiting application...")
                break
            elif key == ord('t'):
                hud.tare_scale()
            elif key == ord('n'):
                hud.next_step()
            elif key == ord('p'):
                hud.prev_step()
            elif key == ord('e'):
                hud.toggle_emergency_stop()

            frame_idx += 1
            if "AGRI_TEST_FRAMES" in os.environ and frame_idx >= int(os.environ["AGRI_TEST_FRAMES"]):
                print(f"[TEST] Successfully rendered {frame_idx} frames. Verification passed!")
                break

    finally:
        if camera_available:
            cap.release()
        engine.close()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    run_controller()
