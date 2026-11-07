# 60-Second Demo Video Script & Hackathon Submission Guide

Use this script to record the mandatory 60-second demonstration video for TinkerHub Saturday Hack Night (Season 02: AgriTech & Food).

---

## ⏱️ Video Breakdown (0:00 – 1:00)

### 1. The Hook & Problem (0:00 – 0:10)
* **Speaker (Member 1 / Adithiyan):**  
  > *"Hi everyone! In farm sorting sheds and commercial kitchens, workers handle muddy produce, raw ingredients, and wet packaging. Touching scales or recipe tablets causes severe cross-contamination and destroys expensive hardware. Here is **AgriTouchless** — a 100% edge-computed touchless controller."*

### 2. Feature 1: Closed Fist Scale Tare (0:10 – 0:25)
* **Visual Action:**  
  * Hold a single **Closed Fist** up in front of the camera.
  * Show the Amber circular dwell progress ring charging around the wrist.
  * At $1.0\text{ s}$, the audio beep plays and the Digital Scale resets from $1,250\text{ g}$ to $0.0\text{ g}$.
* **Speaker (Member 2 / Jazeem):**  
  > *"When weighing produce, a worker simply holds a closed fist for one second. Watch the circular dwell progress ring fill up — the digital scale instantly zeroes out without touching any surface."*

### 3. Feature 2: SOP & Recipe Navigation via Swipes (0:25 – 0:40)
* **Visual Action:**  
  * Raise an **Open Palm** and swipe briskly to the right.
  * The SOP card advances to Step 3/5 with audio chirp.
  * Swipe to the left to return to Step 2/5.
* **Speaker (Member 1 / Adithiyan):**  
  > *"Next, to navigate standard operating procedures or recipes, the worker swipes left or right with an open palm. Our 5-frame velocity buffer and 0.8-second cooldown ensure deliberate steps without accidental bounce-back triggers."*

### 4. Feature 3: Two-Hand Fail-Safe Emergency Stop (0:40 – 0:52)
* **Visual Action:**  
  * Raise **Both Open Palms** simultaneously in a "Hands Up" gesture.
  * Screen flashes with Crimson Red emergency banner: *"EMERGENCY STOP ACTIVATED"*.
  * Timers and scale simulation immediately freeze.
  * Raise both open palms again to resume system.
* **Speaker (Member 2 / Jazeem):**  
  > *"For kitchen and farm machinery safety, raising both open palms immediately triggers an Emergency Stop. All timers freeze, a high-contrast visual alert flashes, and the machinery pause relay engages instantly."*

### 5. Wrap-up & Architecture (0:52 – 1:00)
* **Speaker (Member 1 / Adithiyan):**  
  > *"AgriTouchless runs entirely on local CPU at 30+ FPS using MediaPipe and Euclidean palm normalization for distance invariance. Clean hands, clean food, safe workers. Thank you!"*

---

## 📋 Hackathon Submission Form Copy-Paste Template

* **Project Title:** AgriTouchless: Farm & Kitchen Hygiene Controller
* **Tagline:** Real-time edge computer vision controller for touchless scale taring, recipe navigation, and emergency pauses in dirty-hand food environments.
* **Theme:** Season 02 — Agriculture & Food (AgriTech & Food)
* **GitHub Repository:** `https://github.com/adithiyan-vr/AgriTouchless`
* **Branch:** `Gemini`
* **Tech Stack:** Python 3.10, MediaPipe (Hands Solutions), OpenCV, NumPy, Pygame
* **Key Innovations:**
  1. **Euclidean Palm Normalization:** Gestures scale dynamically with $d_{\text{palm}} = \sqrt{(x_9-x_0)^2 + (y_9-y_0)^2}$ to work seamlessly from 0.5m to 2.0m away.
  2. **5-Frame Rolling Deque Velocity Filter:** Computes horizontal wrist velocity $\frac{dx}{dt}$ with cooldown debouncing to eliminate reverse swipe false positives.
  3. **Multi-Hazard Safety:** Two-hand fail-safe emergency stop designed specifically for agricultural machinery and food prep timers.
