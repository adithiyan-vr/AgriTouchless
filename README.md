# AgriTouchless: Farm & Kitchen Hygiene Controller

> **TinkerHub Saturday Hack Night (Season 02 Focus — AgriTech & Food)**  
> Real-Time, Edge-Computed Touchless Gesture Interface for Dirty-Hand Agricultural Sorting Sheds and Commercial Kitchens.

[![Python](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Hands_Solutions-orange.svg)](https://developers.google.com/mediapipe)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer_Vision-green.svg)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 📌 Problem Statement

In agricultural sorting sheds, greenhouse packing lines, and commercial food preparation kitchens, workers frequently handle wet produce, soil, raw meat, or oily ingredients. Touching digital scales, recipe tablets, or machinery control switches introduces:
1. **Severe Cross-Contamination Risks:** Bacterial transfer across food batches.
2. **Hardware Degradation:** Wet, abrasive dirt destroys capacitive touchscreens and mechanical switches.
3. **Workflow Friction:** Constant degloving, handwashing, or wiping down surfaces slows sorting and packing speeds.

## 💡 Solution Overview

**AgriTouchless** is a low-latency ($< 50\text{ ms}$), camera-based touchless gesture controller executing on local CPU edge hardware. Powered by MediaPipe 21-landmark hand tracking, it enables agricultural workers and culinary staff to:
* **Tare / Zero digital scales** with a closed fist dwell gesture.
* **Navigate SOPs & recipe checklists** using dynamic wrist swipes.
* **Trigger an immediate emergency stop** using a two-hand fail-safe pose.

---

## 👥 Team & Role Allocation

| Member | Role | GitHub Handle | Primary Ownership |
| :--- | :--- | :--- | :--- |
| **Member 1** | Computer Vision & Gesture Lead | [`@adithiyan-vr`](https://github.com/adithiyan-vr) | [`gesture_engine.py`](gesture_engine.py) |
| **Member 2** | Application State, HUD & Audio Lead | [`@jazeemanwar`](https://github.com/jazeemanwar) | [`hud_controller.py`](hud_controller.py) & [`main.py`](main.py) |

---

## 🎯 Gesture Mapping & System Actions

| Gesture | Landmark Logic | Heuristic / Formula | Action Triggered |
| :--- | :--- | :--- | :--- |
| **Closed Fist** | Tips $(8, 12, 16, 20)$ vs. PIPs $(6, 10, 14, 18)$ | Tip $y >$ PIP $y$ for all 4 fingers held for $30\text{ frames}$ ($1.0\text{ s}$) | **Tare / Zero Digital Scale** to $0.0\text{ g}$ |
| **Swipe Right** | Wrist $(0)$ horizontal coordinate ($x$) | $v_x = \frac{x_t - x_{t-5}}{\Delta t} > 0.55$ with `OPEN_PALM` pose | **Next SOP / Recipe Step** |
| **Swipe Left** | Wrist $(0)$ horizontal coordinate ($x$) | $v_x = \frac{x_t - x_{t-5}}{\Delta t} < -0.55$ with `OPEN_PALM` pose | **Previous SOP / Recipe Step** |
| **Two-Hand Stop** | Both hands detected simultaneously | Both hands in `OPEN_PALM` held for $\ge 12\text{ frames}$ | **Toggle Machinery / Timer EMERGENCY STOP** |

---

## 📐 Core Computer Vision Algorithms

### 1. Distance-Independent Euclidean Palm Normalization
To ensure gestures operate reliably whether the user stands $0.5\text{ m}$ or $2.0\text{ m}$ away from the webcam, all landmark coordinates are translated relative to the Wrist ($P_0$) and scaled by the Euclidean palm reference distance between the Wrist ($P_0$) and the Middle Finger MCP ($P_9$):

$$d_{\text{palm}} = \sqrt{(x_9 - x_0)^2 + (y_9 - y_0)^2}$$

$$\hat{x}_i = \frac{x_i - x_0}{d_{\text{palm}}}, \quad \hat{y}_i = \frac{y_i - y_0}{d_{\text{palm}}}$$

### 2. 5-Frame Rolling Deque for Velocity & Bounce-Back Suppression
Horizontal wrist velocity is calculated across a 5-frame rolling window (`collections.deque(maxlen=5)`):

$$v_x = \frac{x_{\text{curr}} - x_{\text{oldest}}}{t_{\text{curr}} - t_{\text{oldest}}}$$

To eliminate accidental triggers when retracting the hand back to the center of the frame:
* Enforces a strict **$0.8\text{ s}$ gesture cooldown timer**.
* Requires the hand to remain in an `OPEN_PALM` pose during the swipe.
* Automatically purges the deque buffer upon firing.

### 3. Circular Dwell-Time Debouncing
Accidental tare triggers are prevented by an incrementing dwell counter $c \in [0, 30]$. An Amber progress arc is dynamically rendered from $0^\circ$ to $360^\circ \times \frac{c}{30}$ around the user's wrist. The tare action commits only when $c = 30$, followed by a $1.5\text{ s}$ cooldown.

---

## 🖥️ Heads-Up Display (HUD) Interface

The dashboard blends a live $1280 \times 720$ camera feed with semi-transparent charcoal panels ($\alpha = 0.65$):
* **Top Status Bar:** Displays real-time operational state (`SYSTEM: RUNNING` in Emerald Green or `SYSTEM: EMERGENCY STOP` in Crimson Red), live FPS, hand detection count, and recognized gesture.
* **Digital Scale Simulator:** Displays live weight in grams with realistic sensor jitter and tare state.
* **Active SOP / Recipe Card:** Displays step progression (e.g. `Step 2/5`), step elapsed timer, and procedure instructions.
* **Emergency Banner & Full-Screen Alert:** Flashing red alert overlay pausing all timers and simulated machinery when emergency stop is engaged.

---

## 🚀 Quickstart & Installation

### Prerequisites
* Python 3.10 (Recommended for pre-built MediaPipe binaries)
* USB / Built-in Webcam (or runs in synthetic demo mode if no camera is connected)

### 1. Clone & Set Up Environment
```powershell
git clone https://github.com/adithiyan-vr/AgriTouchless.git
cd AgriTouchless

# Create and activate virtual environment
py -3.10 -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Touchless Controller
```powershell
python main.py
```

### 3. Keyboard Simulation Shortcuts (For Testing / Demo)
| Key | Action |
| :--- | :--- |
| `t` | Manual Scale Tare / Zero |
| `n` | Advance to Next SOP Step |
| `p` | Return to Previous SOP Step |
| `e` | Toggle Emergency Stop |
| `q` / `ESC` | Exit Application |

---

## 🧪 Automated Test Suite

AgriTouchless includes a comprehensive unit and integration test suite verifying landmark normalization, static pose heuristics, dynamic velocity tracking, two-hand fail-safe detection, and HUD state rendering:

```powershell
python test_agritouchless.py
```

```text
Ran 6 tests in 0.390s
OK
```

---

## 📂 Project Architecture

```text
AgriTouchless/
├── main.py                  # Main loop integrating Vision & HUD Controller
├── gesture_engine.py        # Member 1: MediaPipe setup, palm math, velocity tracking
├── hud_controller.py        # Member 2: State machine (Scale, Recipe, E-Stop) & OpenCV HUD
├── test_agritouchless.py    # Master unit and integration test suite
├── requirements.txt         # mediapipe, opencv-python, numpy, pygame
├── docs/                    # Canonical documentation (PRD, Design, Architecture, Members, Log)
└── Artifacts/               # Hackathon planning and specification artifacts
```

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
