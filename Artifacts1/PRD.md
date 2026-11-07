# PRD — FieldHand: Touchless Farm Machinery & Kitchen Hygiene Controller

| Field | Value |
|---|---|
| Document | `PRD.md` v0.1 (Hack Night draft) |
| Event | Saturday Hack Night — MediaPipe, **Season 02: Agriculture & Food** |
| Build date | Saturday, 7 November 2026 |
| Build window | 6 hours. **H0 = kickoff time: `__:__`** (fill in; all deadlines are relative to H0) |
| Product owner | Member 1 (see `Members.md`) |
| Related docs | `Design.md` · `Architecture.md` · `To-Do.md` · `Log.md` · `Members.md` |

> **Why this project?** Season 02 asks for something that solves a problem in Agriculture & Food using MediaPipe. Of the ideas on the board, *Touchless Farm Machinery & Kitchen Hygiene Controller* is the one that is both inside that focus area and built directly on MediaPipe hand tracking. It is rated Intermediate, so the scope below is deliberately trimmed to fit a 6-hour prototype. (If the team prefers the Beginner idea, *AgriVision*, the same document set can be reused: swap the feature table and gesture table.)

> **Mandatory submission rule:** commit every change before making another move. Commit history is verified during project evaluation. This is treated as a hard project constraint (C-1) and is built into `To-Do.md`, `Log.md` and `Members.md`.

---

## 1. Project Overview

### 1.1 Title
**FieldHand** — a touchless gesture controller for dirty farm sheds, greenhouses and commercial kitchens.

### 1.2 Description and value proposition
FieldHand turns an ordinary laptop webcam into a hands-free control panel for places where hands are wet, muddy, greasy or gloved. Using MediaPipe hand tracking, it lets a person:

- **swipe** to move through recipe or task steps,
- **hold an open palm** to zero (tare) a digital scale,
- **make a fist** to pause a machine or food-prep timer, and
- **raise both hands** to trigger an instant emergency stop,

all without touching a screen, switch or button.

| Value | How FieldHand delivers it |
|---|---|
| Hygiene | Fewer touch points (screens, switches, tablets) means fewer cross-contamination surfaces. |
| Safety-first behaviour | Stopping is fast and forgiving; starting again is slow and deliberate (fail-safe asymmetry). |
| Low cost, low friction | Runs on a laptop and webcam. No cloud, no accounts, no GPU. |
| Privacy | All processing is on-device. Camera frames are never saved or transmitted. |

### 1.3 Problem statement
In farm sheds, greenhouses and commercial kitchens, wet or muddy hands make touching screens and physical switches unhygienic, damaging, or unsafe. Workers either contaminate surfaces, stop to wash and dry their hands, or avoid using digital tools at all.

### 1.4 Target audience

| | Hack-night builders (audience for this build) | Farm-shed / greenhouse operator (end user) | Commercial kitchen cook (end user) |
|---|---|---|---|
| **Demographics** | Ages ~18–35; students and early-career developers; comfortable with Python basics; laptop with webcam | Ages ~25–55; small and mid-size farms and packing sheds; mixed digital literacy; often outdoors or semi-outdoors | Ages ~20–45; restaurants, cloud kitchens, catering; fast-paced, shared equipment |
| **Psychographics** | Curious, build-to-learn, motivated by a working demo in one evening; values clear docs and quick wins | Pragmatic and time-poor; skeptical of tech that adds steps; values robustness over novelty | Hygiene-conscious and rule-bound; values speed; already uses timers, scales and recipe screens |
| **Core need** | A scoped, beginner-friendly path to a convincing MediaPipe prototype | Control machinery or read instructions without removing gloves or cleaning hands | Advance recipes, zero scales and stop timers without touching shared surfaces |
| **Key frustration** | Scope creep, setup friction, unclear acceptance criteria | Screens smeared with mud, switches out of reach, stopping work to wipe hands | Tablets coated in food residue, cross-contamination risk, interrupted workflow |

### 1.5 Goals (specific and measurable)

| ID | Goal | Target | How we know |
|---|---|---|---|
| G1 | Working end-to-end prototype (webcam → gesture → action → on-screen feedback) | Runs with one command: `python main.py` | Fresh-clone dry run (T-27) |
| G2 | Reliable recognition of the 5 gesture commands | ≥ 90 % success per gesture over 20 trials each, normal indoor light | Trial table in `Log.md` (T-22) |
| G3 | Fast emergency stop | ≤ 300 ms from first qualifying frame to ESTOP state | `events.csv` timestamps (T-25) |
| G4 | Smooth real-time performance | ≥ 24 FPS average on a mid-range laptop CPU | FPS counter and event log |
| G5 | Low false-trigger rate | ≤ 1 unintended command in 5 minutes of scripted normal movement (reaching, stirring, wiping) | Idle test (T-23) |
| G6 | Verifiable commit history | 0 uncommitted changes at freeze; at least one commit per completed task | `git status` and `git log` audit (T-29) |
| G7 | Convincing demo | Full scenario in ≤ 3 minutes without restarting | Timed rehearsal (T-28) |

### 1.6 Constraints, assumptions, and non-goals

**Constraints**

| ID | Constraint |
|---|---|
| C-1 | Commit every change before making another move (mandatory submission rule). |
| C-2 | 6-hour build window; Python (JavaScript is allowed by the event but not used here). |
| C-3 | Beginner-friendly stack: MediaPipe, OpenCV, NumPy. No backend, database or cloud. |
| C-4 | Hardware: one laptop webcam per machine. No external devices. |

**Assumptions**

- Team of 2 (Member 1 and Member 2). Names are placeholders until filled in `Members.md`.
- Normal indoor lighting, user 0.5–1.5 m from the camera, one primary operator at a time.
- "Machinery" is **simulated** (a timer and state indicator). No real equipment is controlled.

**Non-goals and safety disclaimer**

> FieldHand is a hack-night prototype. It is **not a certified safety system** and must never replace a physical emergency stop. The E-STOP gesture is a demonstration of a fail-safe interaction pattern only.

---

## 2. Scope

### 2.1 Gesture command set (single source of truth)

| Gesture | Condition | Command | Accepted in state |
|---|---|---|---|
| Swipe right | Open palm, fast horizontal wrist motion, cooldown 0.8 s | `NEXT_STEP` | RUNNING |
| Swipe left | Same as above, opposite direction | `PREV_STEP` | RUNNING |
| Open palm, held still | 1.0 s dwell | `TARE` | RUNNING |
| Closed fist | 0.5 s dwell | `PAUSE` | RUNNING |
| Two hands up | Both open palms, both wrists in upper 40 % of frame, 3 consecutive frames | `ESTOP` (latched) | RUNNING, PAUSED |
| Open palm, held still | 2.0 s dwell from PAUSED; 3.0 s from ESTOP | `RESUME` | PAUSED, ESTOP |

**Priority when gestures overlap:** `ESTOP` > `PAUSE` > `RESUME` / `TARE` > swipe.
**Design rule (fail-safe asymmetry):** a false stop is acceptable; a false start is not. Stop paths are fast; resume paths are slow and deliberate.

### 2.2 Features (MoSCoW)

#### Must have

| ID | Feature | Description | Acceptance criteria |
|---|---|---|---|
| F-01 | Live camera feed | Open webcam, mirror the image (selfie view), request 1280×720 | Preview opens in < 3 s; moving right in real life moves right on screen |
| F-02 | MediaPipe hand tracking | Track up to 2 hands, draw skeleton overlay | Skeleton follows hand at ≥ 24 FPS |
| F-03 | Pose classifier | Classify OPEN_PALM, CLOSED_FIST, OTHER using finger-extension heuristics | ≥ 90 % correct on recorded fixtures and live trials |
| F-04 | Swipe detection | Wrist velocity normalised by palm width, with cooldown | Intentional swipes register; resting-arm drift does not |
| F-05 | Dwell timer and progress ring | Show progress before any dwell command commits; reset on movement or pose change | Ring visible within 100 ms of pose recognition; no partial commits |
| F-06 | Safety state machine | States RUNNING / PAUSED / ESTOP with arbitration and resume rules | All transitions covered by table-driven tests |
| F-07 | Two-hand E-STOP | "Hands up" triggers immediate latched stop | ESTOP within 300 ms of first qualifying frame |
| F-08 | Simulated devices | Recipe stepper (6 steps), digital scale with tare, machine cycle timer | Each device visibly reacts to its command |
| F-09 | HUD | Status chip, panels, hint strip, toasts, FPS (see `Design.md` W2–W5) | Matches wireframes; readable from 2 m |
| F-10 | One-command run and README | `requirements.txt`, README with install, gestures, limits, disclaimer | Stranger reaches skeleton on screen in ≤ 5 min |
| F-11 | Commit discipline (process feature) | Commit after every change; log commit hash in `Log.md` | `git status` clean at freeze; audit passes |

#### Should have

| ID | Feature | Description |
|---|---|---|
| F-12 | CSV event log | Timestamped events (gesture, state change, latency) for metrics |
| F-13 | Camera watchdog | No frames for 1 s forces PAUSED with "CAMERA LOST" banner |
| F-14 | Central config and debug overlay | All thresholds in `config.py`; `D` key shows pose label and wrist velocity |
| F-15 | Help overlay | `H` key shows gesture cheat sheet (W6) |
| F-16 | Unit tests on recorded fixtures | Landmark JSON fixtures for pose classifier and synthetic swipe trajectories |

#### Could have (only after every Must is done)

| ID | Feature | Description |
|---|---|---|
| F-17 | 10-second calibration | Record baseline hand size and distance at startup |
| F-18 | Audible cue | Short beep on PAUSE and ESTOP via preloaded WAV (`pygame.mixer`) |
| F-19 | Session summary screen | Duration, commands, avg FPS, slowest E-STOP (W7) |
| F-20 | Glove and wet-hand test | Document recognition with gloves, wet hands, different lighting |
| F-21 | Demo capture | Short GIF or video of the demo scenario |
| F-22 | Gesture Recognizer comparison | Compare heuristics against MediaPipe's pretrained Gesture Recognizer (Tasks API) |

#### Won't have (this hack night)

- Control of real machinery (relay, GPIO, serial, MQTT). The `DeviceAdapter` interface leaves a clean path for it.
- Custom model training (MediaPipe Model Maker).
- Multi-person tracking or per-user profiles.
- Cloud sync, accounts, analytics or telemetry.
- Mobile app, browser port, or voice control.
- Produce grading (that is the AgriVision idea; a natural next Saturday).
- Any claim of safety certification.

### 2.3 User stories

| ID | User story | Acceptance criteria | Features | Priority |
|---|---|---|---|---|
| US-01 | As a **cook with wet hands**, I want to swipe to move through recipe steps so that I never touch the screen. | *Given* RUNNING state, *when* I swipe right at normal speed, *then* the next step shows within 300 ms and a toast confirms. Resting my arm does not advance a step. | F-04, F-08, F-09 | Must |
| US-02 | As a **cook weighing ingredients**, I want to hold an open palm to zero the scale so that I can add the next ingredient without touching the scale or laptop. | *Given* RUNNING state and one open palm held still, *when* the ring completes at 1 s, *then* the scale reads 0 g. Moving the hand before 1 s cancels it. | F-03, F-05, F-08 | Must |
| US-03 | As a **machine operator**, I want to raise both hands to stop the machine instantly so that I can react even if I cannot reach a switch. | *Given* any non-ESTOP state, *when* both open palms are raised above the upper-40 % line for 3 frames, *then* ESTOP latches in ≤ 300 ms and the machine timer freezes. | F-06, F-07 | Must |
| US-04 | As an **operator with one free hand**, I want to make a fist to pause the machine so that I can interrupt a cycle without a full emergency stop. | *Given* RUNNING state, *when* I hold a fist for 0.5 s, *then* state becomes PAUSED and the timer freezes. | F-03, F-05, F-06 | Must |
| US-05 | As a **supervisor**, I want restarting to require a deliberate action so that a stray movement can never restart the machine. | *Given* PAUSED (or ESTOP), *when* I hold an open palm for 2 s (or 3 s), *then* state returns to RUNNING. All other gestures are ignored while stopped. | F-05, F-06 | Must |
| US-06 | As a **first-time user**, I want to see why nothing happened (progress ring, hint strip, help overlay) so that I can learn the gestures without a manual. | *Given* a partially completed gesture, *then* the ring shows progress and resets visibly. Pressing `H` shows the cheat sheet. | F-05, F-09, F-15 | Should |
| US-07 | As a **hack-night judge**, I want to run the project in one command and inspect a clean commit history so that I can verify the work quickly and fairly. | *Given* a fresh clone, *when* I follow the README, *then* the app runs. `git log` shows incremental, meaningful commits. | F-10, F-11, F-12 | Must |

### 2.4 Demo scenario (≤ 3 minutes)

| Time | Step | Shows |
|---|---|---|
| 0:00 | Launch app, camera check passes, press SPACE | F-01, F-02, F-10 |
| 0:15 | Swipe through 3 recipe steps, then back one | US-01 |
| 0:45 | Place "bowl" (press `W` to add weight), hold palm to tare | US-02 |
| 1:10 | Make a fist: machine PAUSED. Hold palm 2 s to resume | US-04, US-05 |
| 1:50 | Raise both hands: E-STOP. Hold palm 3 s to reset | US-03, US-05 |
| 2:30 | Show `events.csv` and `git log --oneline` | US-07 |

---

## 3. Success Criteria

### 3.1 Hack-night acceptance KPIs (measured before freeze)

| ID | KPI | Target | Measured by | Goal |
|---|---|---|---|---|
| K1 | Gesture success rate (per gesture) | ≥ 90 % over 20 trials | Trial table in `Log.md` | G2 |
| K2 | E-STOP reaction time | ≤ 300 ms (first qualifying frame → ESTOP state) | `events.csv` timestamps | G3 |
| K3 | Frame rate | ≥ 24 FPS average | On-screen counter, session summary | G4 |
| K4 | False triggers | ≤ 1 unintended command per 5 min of normal work | Idle test (T-23) | G5 |
| K5 | Time-to-run for a stranger | ≤ 5 min from `git clone` to hand skeleton | Fresh-clone dry run (T-27) | G1 |
| K6 | Commit discipline | Clean tree at freeze; ≥ 1 commit per completed task | `git status` and `git log` audit | G6 |
| K7 | Demo length | ≤ 3 min, no restarts | Timed rehearsal | G7 |

### 3.2 Post-launch KPIs (2 weeks after hack night)

"Launch" here means the hack-night submission. Targets are starting baselines and should be revisited after the first pilot.

| KPI | Target | Method |
|---|---|---|
| Pilot sessions with real target users | ≥ 5 people from kitchen, farm or lab settings | Observed 10-minute sessions |
| Unaided task completion (swipe, tare, pause, resume) | ≥ 80 % | Observer checklist |
| Usability | SUS score ≥ 70 | 10-item System Usability Scale questionnaire |
| Perceived usefulness ("I would use this at work") | ≥ 4 / 5 average | One-question survey |
| Qualitative feedback | ≥ 3 short interviews; top-3 pain points documented | Notes recorded in `Log.md` |
| Repository engagement | Track stars, forks, clones and issues opened | GitHub Insights (baseline, no fixed target) |
| Iteration velocity | ≥ 1 follow-up release addressing the top pain point | Commit history and tags |

### 3.3 Definition of Done (project level)

- [ ] All Must features (F-01 to F-11) meet their acceptance criteria.
- [ ] KPIs K1–K7 measured and recorded in `Log.md` (misses explained, not hidden).
- [ ] README complete, including known limitations and the safety disclaimer.
- [ ] `git status` is clean and `git log --oneline` tells the story of the build.
- [ ] Tag `v0.1-hacknight` pushed.

### 3.4 Risks and mitigations

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Poor lighting or glare reduces tracking quality | Medium | High | Test at H+1:00; raise detection confidence only after testing; add lighting tip to README |
| R2 | Gloves or mud occlude landmarks | High | Medium | Document as a known limitation; test gloves as a Could (F-20) |
| R3 | False E-STOP from stray hand motion | Medium | Low (fail-safe) | 3-frame confirmation, upper-40 % zone, two hands required |
| R4 | Accidental swipes when resting an arm | High | Medium | Velocity threshold, cooldown, open-palm shape required |
| R5 | Scope creep from the Intermediate idea | High | High | MoSCoW frozen at H+0:30; Could items only after all Must items are done |
| R6 | MediaPipe / Python version install problems | Medium | High | Setup gate at H+0:30; use Python 3.10–3.12 (verify wheel support); fall back to the other machine |
| R7 | Forgetting to commit between changes | Medium | High (evaluation rule) | Clean-tree gate before every new task; audits at H+3:00 and H+5:50 |
| R8 | Prototype mistaken for a real safety system | Low | High | Disclaimer in README, W5 overlay and demo script |

### 3.5 Open questions

1. What is the exact kickoff time (H0)? Fill in at the top of this file and in `To-Do.md`.
2. Are there more than 2 team members? If so, see "Scaling the team" in `Members.md`.
3. Does the event require JavaScript, or is Python acceptable? (The event listing says Python / JavaScript.)
