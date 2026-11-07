# To-Do.md — FieldHand Task Plan

| Field | Value |
|---|---|
| Document | `To-Do.md` v0.1 |
| Date | Saturday, 7 November 2026 |
| Kickoff (H0) | **`__:__`** (fill in). Deadlines below are `H0 + offset`, so `H+1:30` means 1 hour 30 minutes after kickoff. |
| Freeze | `H+6:00` |
| Task board owner | Member 2 (updates the Status column at every check-in) |
| Team | Member 1 = Product & UX Lead · Member 2 = Tech Lead & Delivery (see `Members.md`) |

> **Rule R-01 (mandatory submission rule):** commit every change before making another move. Every task below ends with a commit. Do not start a new task while `git status` shows uncommitted work.

**Status key:** `[ ]` not started · `[~]` in progress · `[x]` done and committed

---

## 1. Task Breakdown

Format per task: **Task name: description · Assigned to · Deadline · Dependencies · Done when**. Task IDs are referenced in `PRD.md`, `Design.md`, `Log.md`.

### Phase 0 — Kickoff and setup (H+0:00 → H+0:30)

| ID | Task | Assigned to | Deadline | Depends on | Done when | Status |
|---|---|---|---|---|---|---|
| T-01 | **Repo setup:** create repo, `.gitignore` (`.venv`, `__pycache__`, `logs/`), commit the six planning docs, push | Member 2 | H+0:15 | none | `git log` shows first commit; teammate can clone. Commit: `docs: add planning documents` | [ ] |
| T-02 | **PRD review:** read PRD together, freeze MoSCoW scope, log the decision in `Log.md` | Member 1 | H+0:30 | T-01 | Scope frozen; Must list agreed; `Log.md` entry committed | [ ] |
| T-03 | **Environment gate:** create venv, install `mediapipe opencv-python numpy pytest`, run the official 20-line hand-tracker boilerplate on **both** machines, pin versions | Member 2 (leads); Member 1 verifies own machine | H+0:30 | T-01 | Skeleton visible on both machines; `requirements.txt` committed | [ ] |

### Phase 1 — Perception core (H+0:30 → H+1:45)

| ID | Task | Assigned to | Deadline | Depends on | Done when | Status |
|---|---|---|---|---|---|---|
| T-04 | **`capture.py` + `perception.py`:** open camera (`--camera N`), mirror, BGR→RGB, wrap MediaPipe Hands, return `HandFrame` with up to 2 hands | Member 2 | H+1:00 | T-03 | Live skeleton from our own code, ≥ 24 FPS | [ ] |
| T-07 | **`config.py`:** all thresholds from `Architecture.md` §3.3 and the BGR palette from `Design.md` §2.1 | Member 1 | H+1:00 | T-03 | No magic numbers needed elsewhere; committed | [ ] |
| T-08 | **Fixture recorder and debug overlay:** keys `1`/`2` save landmarks as OPEN_PALM / CLOSED_FIST JSON fixtures; `D` shows pose label and wrist velocity | Member 1 | H+1:15 | T-04 | ≥ 10 fixtures per pose in `tests/fixtures/` | [ ] |
| T-05 | **`geometry.py`:** pixel-space conversion, palm width, finger-extended tests | Member 2 | H+1:15 | T-04 | Unit tests pass on fixtures | [ ] |
| T-06 | **`gestures.py` pose classifier:** OPEN_PALM / CLOSED_FIST / OTHER with 3-frame debounce; tests on fixtures | Member 2 | H+1:30 | T-05, T-08 | ≥ 90 % correct on fixtures; `pytest` green | [ ] |

### Phase 2 — Commands and safety (H+1:30 → H+3:00)

| ID | Task | Assigned to | Deadline | Depends on | Done when | Status |
|---|---|---|---|---|---|---|
| T-09 | **Swipe detector:** wrist velocity normalised by palm width, cooldown, OPEN_PALM required; tests with synthetic trajectories | Member 2 | H+2:15 | T-06 | Fast swipes register; slow drift does not | [ ] |
| T-10 | **`dwell.py`:** dwell timer with progress 0–1, drift tolerance, reset rules | Member 2 | H+2:30 | T-06 | Progress resets on movement or pose change | [ ] |
| T-11 | **Hands-up detector:** two open palms, wrists in upper 40 %, 3 frames; records `t_first` for latency | Member 2 | H+2:45 | T-06 | Triggers with two raised palms; not with one | [ ] |
| T-12 | **`safety.py` state machine:** RUNNING/PAUSED/ESTOP, priority, resume rules; table-driven tests for every transition in `Architecture.md` §1.2 | Member 2 | H+3:00 | T-09, T-10, T-11 | All transitions tested; `pytest` green | [ ] |

### Phase 3 — Devices and HUD (H+1:30 → H+4:15, parallel with Phase 2)

| ID | Task | Assigned to | Deadline | Depends on | Done when | Status |
|---|---|---|---|---|---|---|
| T-13 | **`recipe.json` + `SimRecipe`:** "Tomato Salsa", 6 steps; next/prev with bounds | Member 1 | H+2:00 | T-07 | Steps change via method calls | [ ] |
| T-14 | **`SimScale`:** weight reading, `TARE`, keys `W`/`S` add/remove 100 g | Member 1 | H+2:30 | T-07 | Tare zeroes the reading | [ ] |
| T-15 | **`SimMachine`:** 60 s cycle timer, freezes in PAUSED/ESTOP and resumes from the frozen value | Member 1 | H+2:45 | T-07 | Timer behaviour matches state | [ ] |
| T-16 | **`hud.py` base layout (W2):** status chip, recipe card, scale and machine panels, FPS, hint strip, toast | Member 1 | H+3:00 | T-07 | Matches `Design.md` W2 | [ ] |
| T-17 | **HUD dwell ring and skeleton colour (W3)** | Member 1 | H+3:30 | T-10, T-16 | Ring fills and resets visibly | [ ] |
| T-18 | **HUD PAUSED and E-STOP overlays (W4, W5)** including the disclaimer | Member 1 | H+3:45 | T-12, T-16 | Overlays match wireframes | [ ] |
| T-19 | **`main.py` integration:** wire capture → perception → gestures → safety → devices → HUD | Member 2 | H+3:30 | T-12, T-16 | Full gesture-to-action loop works end to end | [ ] |
| T-20 | **`events.py`:** CSV event log (`t_iso, t_mono, event, detail, state_before, state_after, fps, latency_ms`) | Member 2 | H+3:45 | T-19 | `logs/session_*.csv` written | [ ] |
| T-21 | **Camera watchdog (Should, F-13):** no frames for 1 s → PAUSED with "CAMERA LOST" | Member 2 | H+4:15 | T-19 | Unplug test goes to PAUSED | [ ] |

### Phase 4 — Test and tune (H+3:45 → H+5:00)

| ID | Task | Assigned to | Deadline | Depends on | Done when | Status |
|---|---|---|---|---|---|---|
| T-22 | **Gesture trials:** 20 trials per gesture; Member 1 performs, Member 2 observes; fill the table in `Log.md` | Member 1 + Member 2 | H+4:30 | T-19 | K1 recorded for all 5 gestures | [ ] |
| T-23 | **Idle false-trigger test:** 5 minutes of scripted normal movement (reach, stir, wipe, rest arm) | Member 1 | H+4:45 | T-19 | K4 recorded | [ ] |
| T-24 | **Tune thresholds:** one commit per parameter change, before/after noted in `Log.md` | Member 2 | H+5:00 | T-22, T-23 | Targets met or misses documented | [ ] |
| T-25 | **Measure FPS and E-STOP latency** from `events.csv`; record K2 and K3 | Member 2 | H+5:00 | T-20 | Numbers in `Log.md` | [ ] |

### Phase 5 — Ship (H+4:30 → H+6:00)

| ID | Task | Assigned to | Deadline | Depends on | Done when | Status |
|---|---|---|---|---|---|---|
| T-26 | **README.md:** install, run, gesture cheat sheet, lighting tips, known limits, safety disclaimer | Member 1 | H+5:15 | T-19 | Complete and committed | [ ] |
| T-27 | **Fresh-clone dry run (K5):** clone to a clean folder, follow README exactly, time it | Member 2 | H+5:30 | T-26 | ≤ 5 min to skeleton; README fixed if not | [ ] |
| T-28 | **Demo script and two timed rehearsals:** Member 1 leads, Member 2 operates (scenario in `PRD.md` §2.4) | Member 1 + Member 2 | H+5:45 | T-24 | ≤ 3 min, no restarts | [ ] |
| T-29 | **Final audit:** `git status` clean, review `git log --oneline`, push, tag `v0.1-hacknight` | Member 2 | H+5:50 | T-27 | Clean tree; tag pushed | [ ] |
| T-30 | **Submission freeze:** no more changes after this point | Both | H+6:00 | T-29 | Submitted | [ ] |

### Recurring tasks

| ID | Task | Owner | When |
|---|---|---|---|
| R-01 | **Commit after every change**, before starting anything else. Message format in `Members.md`. | Both | Continuous |
| R-02 | Update `Log.md` (with commit hash) after each task | Task owner | After each task |
| R-03 | 10-minute check-in; update Status column in this file; re-confirm scope | Member 2 facilitates | H+2:00, H+4:00, H+5:00 |
| R-04 | Clean-tree gate: run `git status` before starting any new task | Both | Before each task |
| R-05 | Mid-build commit audit: `git log --oneline` shows incremental history | Member 2 | H+3:00 |

### Stretch tasks (start only when T-01 to T-19 are done and committed)

| ID | Task | Feature | Assigned to |
|---|---|---|---|
| S-01 | Help overlay (W6) and session summary (W7) | F-15, F-19 | Member 1 |
| S-02 | Launch / camera-check screen (W1) | F-01 polish | Member 1 |
| S-03 | 10-second calibration | F-17 | Member 2 |
| S-04 | Beep on PAUSE and ESTOP via preloaded WAV | F-18 | Member 2 |
| S-05 | Glove and wet-hand recognition test, notes in `Log.md` | F-20 | Member 1 |
| S-06 | Demo GIF or short video | F-21 | Member 1 |
| S-07 | Compare heuristics with MediaPipe Gesture Recognizer | F-22 | Member 2 |

---

## 2. Team Member Tasks

### Member 1 — Product & UX Lead

| Area | Task | IDs |
|---|---|---|
| **PRD** | Review and freeze scope; own acceptance criteria and demo scenario | T-02, T-28 |
| **Design** | HUD base layout, dwell ring, PAUSED and E-STOP overlays, palette and typography in code | T-07, T-16, T-17, T-18 |
| Devices | Recipe, scale and machine simulations | T-13, T-14, T-15 |
| Test data | Fixture recorder and debug overlay | T-08 |
| Validation | Perform gesture trials; run the idle false-trigger test | T-22, T-23 |
| Docs | README and demo script | T-26, T-28 |

Checklist:

- [ ] T-02 PRD review and scope freeze
- [ ] T-07 `config.py`
- [ ] T-08 fixture recorder and debug overlay
- [ ] T-13 recipe
- [ ] T-14 scale
- [ ] T-15 machine
- [ ] T-16 HUD base
- [ ] T-17 dwell ring
- [ ] T-18 PAUSED / E-STOP overlays
- [ ] T-22 gesture trials (with Member 2)
- [ ] T-23 idle test
- [ ] T-26 README
- [ ] T-28 demo rehearsals (with Member 2)

### Member 2 — Tech Lead & Delivery

| Area | Task | IDs |
|---|---|---|
| **Architecture** | Capture, perception, geometry, gesture engine, state machine, integration loop, logger, watchdog | T-03, T-04, T-05, T-06, T-09, T-10, T-11, T-12, T-19, T-20, T-21 |
| **To-Do management** | Task board upkeep, check-ins, commit audits, final audit and tag | T-01, R-03, R-05, T-27, T-29 |
| Measurement | Tuning and KPI measurement | T-24, T-25 |

Checklist:

- [ ] T-01 repo setup
- [ ] T-03 environment gate
- [ ] T-04 capture and perception
- [ ] T-05 geometry
- [ ] T-06 pose classifier
- [ ] T-09 swipe detector
- [ ] T-10 dwell timer
- [ ] T-11 hands-up detector
- [ ] T-12 state machine
- [ ] T-19 integration loop
- [ ] T-20 event logger
- [ ] T-21 watchdog
- [ ] T-22 gesture trials (with Member 1)
- [ ] T-24 tuning
- [ ] T-25 FPS and latency measurement
- [ ] T-27 fresh-clone dry run
- [ ] T-28 demo rehearsals (with Member 1)
- [ ] T-29 final audit

---

## 3. Timeline at a glance

| Window | Focus | Gate to pass before moving on |
|---|---|---|
| H+0:00 – 0:30 | Setup and scope freeze | Skeleton on both machines; docs committed |
| H+0:30 – 1:45 | Perception core | Pose classifier ≥ 90 % on fixtures |
| H+1:30 – 3:00 | Commands and safety | State machine tests green |
| H+1:30 – 4:15 | Devices and HUD (parallel) | HUD matches W2, W4, W5 |
| H+3:30 – 3:45 | Integration | Gesture-to-action loop works end to end |
| H+3:45 – 5:00 | Test and tune | K1–K5 recorded |
| H+4:30 – 6:00 | Ship | Clean tree, tag pushed, demo ≤ 3 min |

If a gate slips by more than 20 minutes at a check-in, cut from the **Should** and **Could** lists first, never from the safety logic (T-09 to T-12).

## 4. Commit checklist (use at every commit)

- [ ] `git status` showed only the files I meant to change
- [ ] Message follows `type(scope): summary` (see `Members.md`)
- [ ] The change is small enough to describe in one line
- [ ] `Log.md` entry added or updated with the commit hash
- [ ] No force-push, no history rewriting
