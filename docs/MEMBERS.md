# Team Members & Role Allocation

Our team consists of **2 Members** working in parallel during the 6-hour Saturday Hack Night. To prevent Git merge conflicts and maximize velocity, tasks are cleanly separated by module.

---

## Member 1: Computer Vision & Gesture Lead
* **Name:** `Adithiyan V R`
* **GitHub Handle:** `@adithiyan-vr`
* **Primary Ownership:** `gesture_engine.py`
* **Core Responsibilities:**
  1. Set up the MediaPipe Hands pipeline (`max_num_hands=2`, confidence thresholds).
  2. Implement coordinate normalization relative to the wrist landmark (`ID 0`).
  3. Build the static pose detector (`Open Palm` vs. `Closed Fist` using fingertip-to-PIP joint comparisons).
  4. Build the 5-frame rolling buffer (`collections.deque`) to calculate wrist horizontal velocity ($\frac{dx}{dt}$) for left/right swipe recognition.
  5. Implement the Two-Hand `'Hands Up'` fail-safe gesture detector.

---

## Member 2: Application State, UI/HUD & Audio Lead
* **Name:** `Jazeem Anwar`
* **GitHub Handle:** `@jazeemanwar`
* **Primary Ownership:** `hud_controller.py` & `main.py`
* **Core Responsibilities:**
  1. Design and render the OpenCV Heads-Up Display (HUD) using semi-transparent overlays (`cv2.addWeighted`).
  2. Build the **Digital Scale Simulator** (simulated weight fluctuations + `Tare/Zero` reset logic).
  3. Build the **Recipe / SOP Step Manager** (step list, active timer, and step advance/rewind triggers).
  4. Build the **Emergency Stop Fail-Safe Overlay** (flashing red banner + system pause state) and circular dwell-time progress indicator.
  5. Integrate low-latency audio/beep feedback (`pygame.mixer` or system beep) on action triggers.