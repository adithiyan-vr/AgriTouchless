# Technical Architecture Document

## 1. High-Level Pipeline
The application follows a modular, event-driven computer vision pipeline executing entirely on the edge (local CPU) at $30+\text{ FPS}$.

```
[Webcam Input (cv2.VideoCapture)]
        │
        ▼
[Frame Pre-processing (Flip + BGR to RGB)]
        │
        ▼
[MediaPipe Hand Landmarker (21 3D Landmarks x 2 Hands)]
        │
        ├──► [Coordinate Normalizer] (Subtract Wrist ID 0, scale by palm size)
        │
        ▼
[Gesture Engine] ──► 1. Static Classifier (Fist vs. Open Palm)
                 ──► 2. Dynamic Tracker (5-Frame Deque for Wrist Velocity dx/dt)
                 ──► 3. Two-Hand Safety Evaluator (Fail-Safe Pause Check)
        │
        ▼
[State Machine & Action Controller]
  ├── Scale Controller (Tare/Zero & Simulated Load)
  ├── SOP/Recipe Navigator (Step Index & Timer)
  └── Machinery Safety Relay (Running vs. Emergency Halted)
        │
        ▼
[OpenCV HUD Renderer (cv2.addWeighted + Circular Dwell Progress)]
```

## 2. Directory & File Structure
To allow both team members to work in parallel without merge conflicts, the codebase is split into two distinct modules plus a main entry point:

```text
agritouchless-controller/
├── main.py                # Main loop integrating Vision & State/UI
├── gesture_engine.py      # Member 1: MediaPipe setup, landmark math, velocity tracking
├── hud_controller.py      # Member 2: State machine (Scale, Recipe, E-Stop) & OpenCV UI
├── requirements.txt       # mediapipe, opencv-python, numpy, pygame
└── docs/                  # PRD.md, DESIGN.md, ARCHITECTURE.md, MEMBERS.md, TODO.md, LOG.md
```

## 3. Core Algorithms
1. **Distance-Independent Normalization:**
   To ensure gestures work regardless of how close the farmer or chef is to the camera, coordinates are normalized relative to the wrist ($P_0$) and scaled by the Euclidean distance between the Wrist ($P_0$) and Middle Finger MCP ($P_9$):
   $$d_{\text{palm}} = \sqrt{(x_9 - x_0)^2 + (y_9 - y_0)^2}$$
2. **Dwell-Time Debouncing:**
   To prevent accidental tare or emergency toggles, static gestures increment a counter $c \in [0, 30]$. A circular arc is drawn from $0^\circ$ to $360^\circ \times \frac{c}{30}$. The action triggers only when $c = 30$, followed by a $1.5\text{ s}$ cooldown.