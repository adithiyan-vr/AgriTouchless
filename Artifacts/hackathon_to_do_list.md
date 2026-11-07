# Saturday Hack Night — Master To-Do List

> **⚠️ MANDATORY SUBMISSION RULE REMINDER:**  
> Commit every single change before making another move! Both **Member 1** and **Member 2** must push small, frequent commits after completing each checkbox below.

---

## Phase 1: Setup & Boilerplate (Hour 0:00 – 0:45)
- [x] **[Member 1]** Initialize Git repository, create `.gitignore`, and commit project documentation (`docs/*.md`).
- [x] **[Member 2]** Create `requirements.txt` (`mediapipe`, `opencv-python`, `numpy`, `pygame`) and verify virtual environment setup.
- [x] **[Member 1]** Run and commit the 20-line MediaPipe Hand Tracker boilerplate in `main.py` to verify webcam feed.
- [x] **[Member 2]** Create stub files `gesture_engine.py` and `hud_controller.py` with clean class interfaces and commit.

---

## Phase 2: Core Gesture Engine & HUD Layout (Hour 0:45 – 2:30)
- [x] **[Member 1]** Implement `GestureEngine` class in `gesture_engine.py` to extract 21 landmarks per hand. *(Commit)*
- [x] **[Member 1]** Implement finger extension states (comparing Tips `8, 12, 16, 20` against PIP joints `6, 10, 14, 18`) to classify `FIST` and `OPEN_PALM`. *(Commit)*
- [x] **[Member 2]** Implement `HUDController` class in `hud_controller.py` with the semi-transparent top status bar and side panels. *(Commit)*
- [x] **[Member 2]** Add Digital Scale widget (displaying weight in grams and tare status) and SOP/Recipe card widget to the HUD. *(Commit)*

---

## Phase 3: Velocity Tracking & Action Triggers (Hour 2:30 – 4:15)
- [x] **[Member 1]** Add a 5-frame `deque` buffer in `gesture_engine.py` to compute wrist (`ID 0`) velocity $\frac{dx}{dt}$ for `SWIPE_LEFT` and `SWIPE_RIGHT` with cooldown. *(Commit)*
- [x] **[Member 1]** Implement the two-hand fail-safe detector: return `EMERGENCY_STOP` when two open palms are visible simultaneously. *(Commit)*
- [x] **[Member 2]** Implement the circular progress ring around the user's wrist/palm (`cv2.ellipse`) to visualize dwell time for the 1-second Fist Tare command. *(Commit)*
- [x] **[Member 2]** Connect state transitions in `hud_controller.py` (`tare_scale()`, `next_step()`, `prev_step()`, `toggle_emergency_stop()`) with `pygame.mixer` sound effects. *(Commit)*

---

## Phase 4: Integration, Calibration & Polish (Hour 4:15 – 5:30)
- [x] **[Member 1 & Member 2]** Connect `GestureEngine` outputs to `HUDController` actions inside `main.py`. *(Commit)*
- [x] **[Member 1]** Tune velocity thresholds and palm normalization so gestures work reliably from $1\text{ meter}$ away. *(Commit)*
- [x] **[Member 2]** Add full-screen red alert overlay when `EMERGENCY_STOP` is active, freezing all timers and machinery states. *(Commit)*

---

## Phase 5: Testing, Demo Video & Submission (Hour 5:30 – 6:00)
- [x] **[Member 1]** Verify `git log` history to ensure clean, frequent commits from both members.
- [x] **[Member 2]** Update `LOG.md` with final milestones, issues resolved, and demo instructions. *(Commit)*
- [x] **[Member 1]** Implement master automated test suite (`test_agritouchless.py`) validating normalization, poses, velocity, and HUD state (6/6 tests passing).
- [ ] **[Member 1 & Member 2]** Record a 60-second demo video showing Tare, Recipe Swipe, and Two-Hand Emergency Stop, and submit the project!
