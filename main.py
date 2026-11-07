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
from produce_detector import ProduceDetector


def run_controller():
    print("=" * 65)
    print("  AgriTouchless: Farm & Kitchen Hygiene Controller")
    print("  TinkerHub Saturday Hack Night | Season 02: AgriTech & Food")
    print("=" * 65)
    print("Initializing Computer Vision Gesture Engine, Produce Detector & HUD...")

    # Initialize Gesture Engine, Produce Detector, and HUD Controller
    engine = GestureEngine(max_num_hands=2, min_detection_confidence=0.7, min_tracking_confidence=0.5)
    hud = HUDController()
    produce_detector = ProduceDetector(roi_box=(60, 160, 680, 640))

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

    # In-app Video Recorder (Press 'r' to record 60s submission demo)
    is_recording = False
    video_writer = None
    record_start_time = 0.0
    show_help = False

    window_name = "AgriTouchless - Farm & Kitchen Hygiene Controller"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, target_width, target_height)

    print("\nSystem Controls & Gesture Guide:")
    print("  • Closed Fist (Hold 1.0s) : TARE / Zero Digital Scale")
    print("  • Swipe Left / Right      : Previous / Next SOP Recipe Step")
    print("  • Two-Hand 'Hands Up'     : Toggle EMERGENCY STOP / Machinery Pause")
    print("  • Press 'a'               : Toggle Farmer Automation Engine (Auto-Portion & Crate Tally)")
    print("  • Press 'r'               : Start/Stop 60s Demo Video Recording (submission_demo.mp4)")
    print("  • Press 'h'               : Toggle On-Screen Controls Cheatsheet")
    print("  • Keyboard shortcuts      : 't' (Tare), 'n' (Next), 'p' (Prev), 'e' (E-Stop), 'a' (Auto), '1'-'6' (Produce), '8'/'u' (Foreign Item), '0' (Clear), 'q' (Quit)\n")

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

            # Run Computer Vision gesture analysis
            analysis = engine.analyze_frame(frame, width=target_width, height=target_height)

            hands_count = analysis["hands_count"]
            primary_gesture = analysis["primary_gesture"]
            action = analysis["action_trigger"]
            dwell_progress = analysis["dwell_progress"]
            dwell_center = analysis["dwell_center"]

            # Extract hand bounding boxes to prevent hand skin false-positives in produce scanner
            hand_bboxes = []
            if analysis["raw_results"].multi_hand_landmarks:
                for hand_lms in analysis["raw_results"].multi_hand_landmarks:
                    xs = [int(lm.x * target_width) for lm in hand_lms.landmark]
                    ys = [int(lm.y * target_height) for lm in hand_lms.landmark]
                    bx1, bx2 = max(0, min(xs) - 25), min(target_width, max(xs) + 25)
                    by1, by2 = max(0, min(ys) - 25), min(target_height, max(ys) + 25)
                    hand_bboxes.append((bx1, by1, bx2 - bx1, by2 - by1))

            # Run Fruit & Vegetable Object Detection & Scale Weight Estimation
            detected_produce = produce_detector.detect_produce(frame, hand_bboxes=hand_bboxes)
            produce_detector.draw_inspection_zone(frame, detected_produce)

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

            # Render complete OpenCV HUD overlay with produce integration
            display_frame = hud.render(
                frame,
                hands_detected=hands_count,
                current_gesture=primary_gesture,
                dwell_progress=dwell_progress,
                dwell_center=dwell_center,
                detected_produce=detected_produce
            )

            # In-App 60s Demo Video Recording Logic
            if is_recording and video_writer:
                elapsed = time.time() - record_start_time
                if elapsed >= 60.0:
                    is_recording = False
                    video_writer.release()
                    video_writer = None
                    print("[RECORDER] 60-second limit reached. Saved submission_demo.mp4!")
                else:
                    # Write frame to MP4
                    video_writer.write(display_frame)
                    # Draw blinking REC indicator
                    if int(elapsed * 2) % 2 == 0:
                        cv2.circle(display_frame, (380, 25), 8, (0, 0, 255), -1, cv2.LINE_AA)
                    cv2.putText(display_frame, f"REC {int(elapsed):02d}s/60s", (395, 32),
                                cv2.FONT_HERSHEY_DUPLEX, 0.55, (0, 0, 255), 2, cv2.LINE_AA)

            # Optional On-Screen Controls Cheatsheet Drawer (Toggle with 'h')
            if show_help:
                help_overlay = display_frame.copy()
                cv2.rectangle(help_overlay, (200, 100), (1080, 620), (20, 20, 20), -1)
                cv2.addWeighted(help_overlay, 0.85, display_frame, 0.15, 0, display_frame)
                cv2.rectangle(display_frame, (200, 100), (1080, 620), (0, 200, 255), 2)
                cv2.putText(display_frame, "AGRITOUCHLESS CHEATSHEET & CONTROLS GUIDE", (230, 145),
                            cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 255, 200), 2, cv2.LINE_AA)
                cheats = [
                    ("Closed Fist (Hold 1.0s)", "Tare / Zero the Digital Scale to 0.0g"),
                    ("Swipe Right (Open Palm)", "Advance to Next SOP / Recipe Step"),
                    ("Swipe Left (Open Palm)", "Return to Previous SOP / Recipe Step"),
                    ("Two-Hand Hands Up", "Toggle EMERGENCY STOP / Machinery Pause"),
                    ("Key 'a'", "Toggle Farm Automation Engine (Auto-Portion & Crate Tally)"),
                    ("Key '1' to '6'", "Simulate Produce: 1=Tomato, 2=Apple, 3=Banana, 4=Carrot, 5=Greens, 6=Potato"),
                    ("Key '8' or 'u'", "Simulate UNKNOWN Foreign Object (Verify Rejection & Interlock)"),
                    ("Key '0' or 'c'", "Clear Scale Platter (Empty)"),
                    ("Key 'r'", "Start / Stop recording 60s demo video (submission_demo.mp4)"),
                    ("Key 't' / 'n' / 'p' / 'e'", "Simulate Tare / Next / Prev / Emergency Stop manually"),
                    ("Key 'h'", "Close this Help Drawer"),
                    ("Key 'q' / ESC", "Exit Application")
                ]
                for idx, (action_k, desc_k) in enumerate(cheats):
                    yy = 190 + idx * 40
                    cv2.putText(display_frame, f"• {action_k}:", (240, yy),
                                cv2.FONT_HERSHEY_DUPLEX, 0.52, (255, 255, 0), 1, cv2.LINE_AA)
                    cv2.putText(display_frame, desc_k, (530, yy),
                                cv2.FONT_HERSHEY_DUPLEX, 0.50, (230, 230, 230), 1, cv2.LINE_AA)

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
            elif key == ord('a'):
                hud.toggle_automation()
            elif key == ord('h'):
                show_help = not show_help
            elif key == ord('r'):
                # Toggle demo recording
                if not is_recording:
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    video_writer = cv2.VideoWriter("submission_demo.mp4", fourcc, 30.0, (target_width, target_height))
                    record_start_time = time.time()
                    is_recording = True
                    print("[RECORDER] Started recording live demo to 'submission_demo.mp4'...")
                else:
                    is_recording = False
                    if video_writer:
                        video_writer.release()
                        video_writer = None
                    print("[RECORDER] Stopped recording. Saved to 'submission_demo.mp4'!")
            elif key in [ord('1'), ord('2'), ord('3'), ord('4'), ord('5'), ord('6')]:
                # Simulate fruit/vegetable placement
                produce_detector.set_simulated_produce(chr(key))
                print(f"[PRODUCE SIMULATION] Placed {produce_detector.current_item.name} on scale")
            elif key in [ord('8'), ord('u')]:
                # Simulate foreign/unknown object placement to verify rejection
                produce_detector.set_simulated_produce("8")
                print("[PRODUCE SIMULATION] Placed UNKNOWN FOREIGN ITEM on scale (Verified Rejection & Interlock)")
            elif key in [ord('0'), ord('c')]:
                # Clear scale platter
                produce_detector.set_simulated_produce("0")
                print("[PRODUCE SIMULATION] Cleared produce from scale platter")

            frame_idx += 1
            if "AGRI_TEST_FRAMES" in os.environ and frame_idx >= int(os.environ["AGRI_TEST_FRAMES"]):
                print(f"[TEST] Successfully rendered {frame_idx} frames. Verification passed!")
                break

    finally:
        if is_recording and video_writer:
            video_writer.release()
        if camera_available:
            cap.release()
        engine.close()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    run_controller()
