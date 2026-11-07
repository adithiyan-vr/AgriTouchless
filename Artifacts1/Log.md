# Log.md — FieldHand Project Log

| Field | Value |
|---|---|
| Document | `Log.md` v0.1 (living document) |
| Purpose | Track progress, issues, decisions and measurements; link every entry to a commit |
| Date | Saturday, 7 November 2026 |
| Kickoff (H0) | `__:__` (fill in) |

> **Why a commit hash in every entry?** The mandatory submission rule says commit history will be verified. Linking each log entry to a commit makes the story easy to check: *what we did*, *why*, and *the exact change*.

## 1. How to log

1. Add an entry **after each task** (and any time something goes wrong). Newest entries go at the bottom of §3.
2. Commit the code first, then log with the commit hash (`git log -1 --format=%h`). Commit the log update as `docs(log): ...`.
3. Be honest: log failures, misses and workarounds. A clear miss with an explanation is better than a hidden one.
4. Keep entries short (2–5 lines). Use the issue table in §5 for anything that stays open.
5. Entries marked **EXAMPLE** are format samples. **Delete them before submission.**

## 2. Entry format (copy and paste)

```markdown
### LOG-NNN — YYYY-MM-DD HH:MM (H+h:mm)
- **Date:** YYYY-MM-DD
- **Team member:** Member 1 | Member 2 | Both
- **Task:** T-xx short name
- **Commit:** `abc1234`
- **Progress / issues:** what happened, what worked, what did not
- **Resolution / next steps:** how it was fixed, or what happens next and who owns it
```

## 3. Log entries

### LOG-001 — 2026-11-07 (planning, before H0)
- **Date:** 2026-11-07
- **Team member:** Both
- **Task:** Planning documents drafted (`PRD.md`, `Design.md`, `Architecture.md`, `To-Do.md`, `Log.md`, `Members.md`)
- **Commit:** `________` (fill in after first commit, T-01)
- **Progress / issues:** Project selected: *Touchless Farm Machinery & Kitchen Hygiene Controller* (named **FieldHand**), because it matches the Season 02 Agriculture & Food focus and is built directly on MediaPipe hand tracking. Scope trimmed with MoSCoW to fit 6 hours. Wireframes, palette, architecture and task plan drafted.
- **Resolution / next steps:** Member 1 reviews and freezes scope at H+0:30 (T-02). Member 2 creates the repo and commits these documents (T-01).

### LOG-002 — EXAMPLE (delete before submission)
- **Date:** YYYY-MM-DD
- **Team member:** Member 1
- **Task:** T-16 HUD base layout (example)
- **Commit:** `abc1234`
- **Progress / issues:** Completed the main HUD layout, but the recipe card text overflowed on long steps.
- **Resolution / next steps:** Limited step text to 2 lines per `Design.md` and shortened the recipe wording. Next: dwell ring (T-17).

### LOG-003 — EXAMPLE (delete before submission)
- **Date:** YYYY-MM-DD
- **Team member:** Member 2
- **Task:** T-09 Swipe detector (example)
- **Commit:** `def5678`
- **Progress / issues:** Swipes triggered when resting the arm on the table.
- **Resolution / next steps:** Raised the minimum speed and required an open palm; added a synthetic-trajectory test for slow drift. Re-test at T-22.

<!-- Add new entries below this line -->

---

## 4. Measurements

### 4.1 Gesture trials (K1, T-22)

20 trials per gesture, same lighting as the demo. Count a trial as a success only if the correct command fires once, and no other command fires.

| Gesture | Trials | Successes | Rate | Target | Notes (lighting, distance, failures) |
|---|---|---|---|---|---|
| Swipe right | 20 | | | ≥ 90 % | |
| Swipe left | 20 | | | ≥ 90 % | |
| Open palm hold (tare) | 20 | | | ≥ 90 % | |
| Closed fist hold (pause) | 20 | | | ≥ 90 % | |
| Two hands up (E-STOP) | 20 | | | ≥ 90 % | |
| Open palm hold (resume) | 20 | | | ≥ 90 % | |

### 4.2 KPI results

| ID | KPI | Target | Result | Pass? | Evidence / commit |
|---|---|---|---|---|---|
| K1 | Gesture success rate | ≥ 90 % each | | | §4.1 |
| K2 | E-STOP reaction time | ≤ 300 ms | | | `logs/session_*.csv` |
| K3 | Average FPS | ≥ 24 | | | Session summary |
| K4 | False triggers in 5 min | ≤ 1 | | | T-23 |
| K5 | Clone-to-skeleton time | ≤ 5 min | | | T-27 |
| K6 | Commit discipline | Clean tree; ≥ 1 commit per task | | | T-29 audit |
| K7 | Demo length | ≤ 3 min | | | T-28 |

### 4.3 Tuning record (T-24)

One row per parameter change; each has its own commit.

| Parameter | Before | After | Reason | Commit |
|---|---|---|---|---|
| | | | | |

### 4.4 Post-launch feedback (2 weeks after hack night)

| Date | Participant (role) | Task completion | SUS | "Would use at work" (1–5) | Top pain point |
|---|---|---|---|---|---|
| | | | | | |

---

## 5. Issue tracker

| ID | Date | Reported by | Issue | Severity | Status | Resolution | Commit |
|---|---|---|---|---|---|---|---|
| I-001 | | | | Low / Med / High | Open / Fixed / Won't fix | | |

Severity guide: **High** blocks a Must feature or the demo · **Med** degrades accuracy or UX · **Low** cosmetic.

## 6. Decision log

Decisions made during planning. Add new rows as the team decides things; never delete old ones (strike through and add a new row instead).

| ID | Date | Decision | Why | Alternatives rejected | Owner |
|---|---|---|---|---|---|
| D-01 | 2026-11-07 | Build **FieldHand**, the Touchless Farm Machinery & Kitchen Hygiene Controller | In the Season 02 focus (Agriculture & Food) and built on MediaPipe hand tracking | AgriVision (Beginner): relies on OpenCV colour masks rather than MediaPipe | Both |
| D-02 | 2026-11-07 | Python + OpenCV HUD, no web UI | Fastest path to a working demo; matches official boilerplate | Browser app with MediaPipe JS | Member 2 |
| D-03 | 2026-11-07 | Use MediaPipe Hands with landmark heuristics for poses | Same API as the boilerplate; transparent and tunable; Gesture Recognizer comparison kept as a Could (F-22) | Gesture Recognizer first (needs a model file and gives less control over thresholds) | Member 2 |
| D-04 | 2026-11-07 | Fail-safe asymmetry: stop fast, restart slowly | Safer failure mode for machinery; accepts false stops over false starts | Symmetric hold times | Member 1 |
| D-05 | 2026-11-07 | Machinery is simulated only | 6-hour scope; no hardware risk | Relay or serial integration | Both |
| D-06 | 2026-11-07 | Team of 2; roles split Product & UX / Tech & Delivery | Matches template and keeps handoffs small | Equal split by feature | Both |
| D-07 | 2026-11-07 | History is never rewritten (no force-push, no squash or rebase of shared commits) | Commit history is verified at evaluation | Squash-on-merge | Member 2 |
