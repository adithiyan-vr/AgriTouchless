# Saturday Hack Night — Build & Commit Log

Use this file to track real-time progress, architectural decisions, and Git commits throughout the 6-hour hack night. Updating and committing this log regularly demonstrates consistent progress and clean engineering velocity during evaluation!

---

## Session Info
* **Date:** Saturday, November 7, 2026
* **Event:** TinkerHub Saturday Hack Night (Season 02: AgriTech & Food)
* **Project:** AgriTouchless: Farm & Kitchen Hygiene Controller
* **Team Members:** Member 1 (`Adithiyan V R` - CV/Gesture Lead) & Member 2 (`Jazeem Anwar` - HUD/State Lead)

---

## Chronological Build Log

| Time | Member | Module / File | Activity & Milestone Reached | Git Commit Message |
| :--- | :--- | :--- | :--- | :--- |
| **19:15** | Member 1 & 2 | `docs/*.md` | Ideated project based on Season 02 AgriTech & Food focus; generated PRD, Design, Architecture, Members, and To-Do docs. | `docs: initialize PRD, architecture, design, members, and todo files` |
| **19:30** | Member 1 | `main.py` | Tested webcam feed and verified MediaPipe 20-line hand tracker boilerplate at 30+ FPS. | `feat(core): add mediapipe hand tracking boilerplate` |
| **19:45** | Member 2 | `hud_controller.py` | Created initial OpenCV overlay layout for Digital Scale and Recipe/SOP cards with semi-transparent charcoal panels. | `feat(ui): create base OpenCV HUD layout for scale and recipe steps` |
| **20:30** | Member 1 | `gesture_engine.py` | Implemented `OPEN_PALM` and `CLOSED_FIST` heuristic detection using landmark fingertip-to-PIP joint Y-coordinates. | `feat(cv): add static fist and open palm gesture recognition` |
| **21:00** | Member 2 | `hud_controller.py` | Added circular dwell-time progress indicator (`cv2.ellipse`) and connected `CLOSED_FIST` to Tare/Zero scale action. | `feat(ui): add circular progress feedback and scale tare action` |
| **21:45** | Member 1 | `gesture_engine.py` | Added 5-frame wrist velocity tracker ($\frac{dx}{dt}$) to detect intentional left/right swipes without resting-arm false triggers. | `feat(cv): implement 5-frame wrist velocity swipe detector` |
| **22:15** | Member 1 | `gesture_engine.py` | Added two-hand `'Hands Up'` fail-safe detection for emergency machinery pause. | `feat(cv): add two-hand open palm emergency stop detector` |
| **22:45** | Member 2 | `main.py` | Integrated `GestureEngine` with `HUDController` and added low-latency audio alerts via `pygame.mixer`. | `feat(app): integrate gesture engine with HUD state machine and audio` |
| **23:00** | Member 1 | `gesture_engine.py` & `test_agritouchless.py` | Calibrated velocity thresholds for distance invariance ($1\text{m} - 2\text{m}$) using palm-scaled velocity and created automated unit & integration test suite (6/6 passing). | `tune(cv): calibrate velocity thresholds and palm normalization for distance sensitivity` |
| **23:15** | Member 1 & 2 | `main.py` | Added automated verification testing hook (`AGRI_TEST_FRAMES`), synthetic camera feed fallback for headless/remote runs, and verified end-to-end execution. | `feat(test): add verification test mode and graceful exit hook` |
| **23:30** | Member 1 & 2 | `README.md` | Crafted comprehensive project documentation with problem statement, system architecture, math models, quickstart, and demo instructions. | `docs(readme): add comprehensive project documentation and setup guide` |
| **23:45** | Member 1 & 2 | `TODO.md` & `LOG.md` | Finalized milestone tracker and build log; verified git history compliance with mandatory submission rules. | `docs: update build log and master to-do list` |
| **00:15** | Member 1 & 2 | `produce_detector.py`, `hud_controller.py`, `gesture_engine.py` | Built Fruit & Vegetable Vision Identifier, dynamic load-cell scale physics, and rotation-invariant Euclidean gesture heuristics. | `feat(vision): add fruit & vegetable identifier, fix digital scale, and harden gesture recognition` |

---

## Issues Encountered & Fixes Applied

* **Issue 1 (Accidental Swipes):** Moving the hand back to the center after swiping right triggered an unwanted left swipe.
  * *Fix (Member 1):* Added a $0.8\text{ s}$ gesture cooldown timer, required the hand to remain in an `OPEN_PALM` pose during the swipe, and immediately cleared the 5-frame deque buffer upon trigger.
* **Issue 2 (Distance Sensitivity):** Hand landmarks and displacement scaled differently when standing $1\text{m} - 2\text{m}$ away from the kitchen counter.
  * *Fix (Member 1):* Normalized landmark coordinates relative to Wrist ($P_0$) and scaled by Euclidean palm reference distance ($P_0$ to Middle MCP $P_9$). Added dual-criterion velocity check evaluating both screen displacement and palm-relative velocity ($\frac{dx / d_{\text{palm}}}{dt} > 3.8\text{ palms/s}$).
* **Issue 3 (MediaPipe Solutions API Compatibility):** Newer MediaPipe versions removed the top-level `mp.solutions.hands` API in favor of Tasks.
  * *Fix (Member 1):* Pinned virtual environment to `mediapipe==0.10.14` with compatible `protobuf==4.25.9` and implemented defensive fallback handling in `GestureEngine` so unit tests execute cleanly across all environments.
* **Issue 4 (Camera Availability in Headless / Remote Testing):** Running verification in environments without a physical webcam connected could throw index errors on `cv2.VideoCapture(0)`.
  * *Fix (Member 2):* Added an automatic synthetic frame generator displaying a dark greenhouse work surface with keyboard shortcuts (`t`, `n`, `p`, `e`, `q`) to allow autonomous testing and seamless evaluation.
* **Issue 5 (Faulty Hand Gesture Angles):** When hands were angled diagonally or pointing toward the camera, 2D Y-coordinate checks produced false negatives or flickering poses.
  * *Fix (Member 1):* Replaced linear Y checks with rotation-invariant 3D Euclidean distance ratios from fingertips to Wrist ($P_0$) and MCP joints. Enforced minimum physical displacement ($|dx| \ge 0.06$) to eliminate camera tremor false swipes, and restricted swipe tracking to single-hand frames to prevent coordinate mixing across alternating hands.
* **Issue 6 (Static Digital Scale & Produce Identification):** Digital scale previously ran on a static baseline without recognizing agricultural harvest items.
  * *Fix (Member 1 & 2):* Implemented [`produce_detector.py`](file:///c:/Users/user/Documents/Hackathon/Thinkerhub/AgriTouchless/produce_detector.py) providing real-time HSV + morphological segmentation for Tomatoes, Apples, Bananas, Carrots, Potatoes, and Leafy Greens. Linked detected produce area directly to load-cell scale physics with realistic settling easing, gross/net readouts, and negative tare offsets.
