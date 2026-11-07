# System & UI/UX Design Document

## 1. Design Philosophy
Because users in farm sheds and kitchens stand $1\text{ to }2\text{ meters}$ away from the screen under varying lighting conditions, the UI must feature **high-contrast elements**, **oversized typography**, and **unambiguous visual/audible feedback**.

## 2. Screen Layout (OpenCV HUD Overlay)
The application runs in a single $1280 \times 720$ window blending the live webcam feed with a clean control dashboard overlay:

```
+-----------------------------------------------------------------------+
| [STATUS BAR]  SYSTEM: RUNNING (GREEN)      FPS: 32     HANDS: 1/2     |
+-----------------------------------+-----------------------------------+
|                                   |  DIGITAL SCALE SIMULATOR          |
|                                   |  Weight:  1,250 g                 |
|                                   |  [Hold Fist 1s to TARE/ZERO]      |
|        LIVE WEBCAM FEED           +-----------------------------------+
|    (with MediaPipe Skeleton       |  ACTIVE SOP / RECIPE STEP (2/5)   |
|     & Circular Gesture Timer)     |  "Wash and sort Grade-A tomatoes  |
|                                   |   into sanitized crate #2."       |
|                                   |  [<< Swipe Left | Swipe Right >>] |
+-----------------------------------+-----------------------------------+
| [EMERGENCY BANNER] Raise BOTH Open Palms to Trigger EMERGENCY STOP    |
+-----------------------------------------------------------------------+
```

## 3. Gesture Mapping & Heuristics

| Gesture | Landmarks Used | Mathematical Condition | Action Triggered |
| :--- | :--- | :--- | :--- |
| **Open Palm** | Wrist ($0$), Fingertips ($8, 12, 16, 20$), PIP Joints ($6, 10, 14, 18$) | Tip $y <$ PIP $y$ for all 4 fingers | Ready state / Used in 2-hand Emergency Stop |
| **Closed Fist** | Fingertips ($8, 12, 16, 20$), PIP Joints ($6, 10, 14, 18$) | Tip $y >$ PIP $y$ for all 4 fingers held for $30\text{ frames}$ | Tare / Reset Digital Scale to $0\text{ g}$ |
| **Swipe Right / Left** | Wrist ($0$) horizontal coordinate ($x$) | Velocity $v_x = \frac{x_t - x_{t-5}}{\Delta t} > \text{Threshold}$ | Next Step / Previous Step in Recipe/SOP |
| **Two-Hand Stop** | Multi-hand detection $= 2$, both hands `Open Palm` | `len(multi_hand_landmarks) == 2` and both Open | Toggle Machinery / Timer **EMERGENCY STOP** |

## 4. Color Palette (BGR Format for OpenCV)
* **Safe / Active State:** Emerald Green `(80, 200, 120)`
* **Gesture Charging / Progress:** Amber Yellow `(0, 191, 255)`
* **Emergency Stop / Alert:** Crimson Red `(60, 20, 220)`
* **HUD Panel Background:** Semi-transparent Charcoal `(30, 30, 30)` with $\alpha = 0.65$