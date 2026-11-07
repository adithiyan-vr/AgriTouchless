# Product Requirements Document (PRD)

## 1. Project Overview
* **Project Name:** AgriTouchless: Farm & Kitchen Hygiene Controller
* **Event:** TinkerHub Saturday Hack Night (6-Hour Prototype)
* **Theme / Focus:** Season 02 Focus — Agriculture & Food (AgriTech & Food)
* **Difficulty Level:** Intermediate
* **Tech Stack:** Python, MediaPipe (Hands Solutions), OpenCV, NumPy

## 2. Problem Statement
In agricultural sorting sheds, greenhouses, and commercial food preparation kitchens, workers frequently have wet, muddy, or contaminated hands. Touching digital scales, recipe terminals, or machinery switches introduces severe cross-contamination hazards, ruins touchscreens, and slows down workflows by requiring constant handwashing or glove changes.

## 3. Solution Overview
A real-time, low-latency, camera-based touchless controller powered by on-device MediaPipe Hand Landmarker. It allows farmers and kitchen staff to zero/tare digital scales, advance through standard operating procedures (SOPs) or recipes, and trigger an immediate fail-safe emergency stop for machinery or timers using simple mid-air hand gestures.

## 4. Target Audience
* **Agricultural Workers:** Sorting produce, weighing harvests, and controlling conveyor belts with muddy or gloved hands.
* **Commercial Kitchen Staff:** Navigating recipes, controlling food timers, and taring scales while handling raw ingredients.

## 5. Core Features (MVP for 6-Hour Hack)
1. **Live Hand Skeleton & Gesture Recognition:**
   * Real-time tracking of 21 3D hand landmarks at $30+\text{ FPS}$ using MediaPipe.
2. **Digital Scale Tare / Zero Command (`Closed Fist`):**
   * Holding a single closed fist for $1.0\text{ second}$ zeroes out the simulated digital weight scale on screen.
3. **Recipe / SOP Step Navigation (`Wrist Swipe Left / Right`):**
   * Dynamic tracking of wrist velocity ($\frac{dx}{dt}$) to advance to the next step or return to the previous step without accidental triggers.
4. **Fail-Safe Emergency Pause (`Two-Hand 'Hands Up' / Open Palms`):**
   * Detecting two open palms raised simultaneously immediately triggers an emergency stop/pause state for machinery and prep timers.
5. **Visual HUD & Circular Progress Feedback:**
   * An OpenCV-rendered Heads-Up Display (HUD) with a circular progress indicator that fills up before confirming a state change, preventing false positives.

## 6. Success Metrics
* **Latency:** Gesture recognition and HUD update in $< 50\text{ ms}$ on local CPU.
* **Accuracy:** Zero false-positive step advances while resting hands or moving slowly.
* **Compliance:** Strict adherence to incremental Git commits after every sub-task (Mandatory Submission Rule).