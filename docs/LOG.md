# Saturday Hack Night — Build & Commit Log

Use this file to track your real-time progress, architectural decisions, and Git commits throughout the 6-hour hack night. Updating and committing this log regularly also helps demonstrate consistent progress during evaluation!

---

## Session Info
* **Date:** Saturday, November 7, 2026
* **Event:** TinkerHub Saturday Hack Night
* **Project:** AgriTouchless: Farm & Kitchen Hygiene Controller
* **Team Members:** Member 1 (CV/Gesture Lead) & Member 2 (HUD/State Lead)

---

## Chronological Build Log

| Time | Member | Module / File | Activity & Milestone Reached | Git Commit Message |
| :--- | :--- | :--- | :--- | :--- |
| **19:15** | Member 1 & 2 | `docs/*.md` | Ideated project based on Season 02 AgriTech & Food focus; generated PRD, Design, Architecture, Members, and To-Do docs. | `docs: initialize PRD, architecture, design, members, and todo files` |
| **19:30** | Member 1 | `main.py` | Tested webcam feed and verified MediaPipe 20-line hand tracker boilerplate at 30+ FPS. | `feat(core): add mediapipe hand tracking boilerplate` |
| **19:45** | Member 2 | `hud_controller.py` | Created initial OpenCV overlay layout for Digital Scale and Recipe/SOP cards. | `feat(ui): create base OpenCV HUD layout for scale and recipe steps` |
| **20:30** | Member 1 | `gesture_engine.py` | Implemented `OPEN_PALM` and `CLOSED_FIST` heuristic detection using landmark Y-coordinates. | `feat(cv): add static fist and open palm gesture recognition` |
| **21:00** | Member 2 | `hud_controller.py` | Added circular dwell-time progress indicator and connected `CLOSED_FIST` to Tare/Zero scale action. | `feat(ui): add circular progress feedback and scale tare action` |
| **21:45** | Member 1 | `gesture_engine.py` | Added 5-frame wrist velocity tracker ($\frac{dx}{dt}$) to detect intentional left/right swipes without resting-arm false triggers. | `feat(cv): implement 5-frame wrist velocity swipe detector` |
| **22:15** | Member 1 | `gesture_engine.py` | Added two-hand `'Hands Up'` fail-safe detection for emergency machinery pause. | `feat(cv): add two-hand open palm emergency stop detector` |
| **22:45** | Member 2 | `main.py` | Integrated `GestureEngine` with `HUDController` and added low-latency audio alerts via `pygame.mixer`. | `feat(app): integrate gesture engine with HUD state machine and audio` |

---

## Issues Encountered & Fixes Applied
* **Issue 1 (Accidental Swipes):** Moving the hand back to the center after swiping right triggered a left swipe.
  * *Fix (Member 1):* Added a $0.8\text{ s}$ gesture cooldown timer and required the hand to be in an `OPEN_PALM` pose during the swipe.
* **Issue 2 (Distance Sensitivity):** Hand landmarks scaled differently when standing far from the kitchen counter.
  * *Fix (Member 1):* Normalized landmark distances using palm size ($\text{Wrist ID } 0$ to $\text{Middle MCP ID } 9$).