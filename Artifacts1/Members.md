# Members.md — Roles and Responsibilities

| Field | Value |
|---|---|
| Document | `Members.md` v0.1 |
| Project | FieldHand — Touchless Farm Machinery & Kitchen Hygiene Controller |
| Event | Saturday Hack Night (Season 02: Agriculture & Food), 7 November 2026 |
| Assigned tasks | Always refer to `To-Do.md` (this file lists responsibilities, not task status) |

> **Placeholders:** fill in the names and handles below at kickoff. If your team has more than two people, see §5.

---

## 1. Team Members

### Member 1 — Product & UX Lead

| Field | Value |
|---|---|
| Name | `[fill in]` |
| GitHub handle | `[fill in]` |
| Contact | `[fill in]` |
| Role | Product owner and experience designer. Owns *what* gets built and *how it feels*. |
| Decision rights | Final say on scope (MoSCoW), acceptance criteria, UX copy, visual design and demo flow. |

**Responsibilities**

- Maintain `PRD.md`: scope, user stories, KPIs; lead the scope freeze at H+0:30 (T-02).
- Maintain `Design.md`: wireframes, palette, typography; implement them in `hud.py` and `config.py` (T-07, T-16, T-17, T-18).
- Build the simulated devices: recipe stepper, scale, machine timer (T-13, T-14, T-15).
- Record landmark fixtures and the debug overlay used by the tests (T-08).
- Perform the gesture trials and the idle false-trigger test (T-22, T-23).
- Write the README and the demo script; lead the demo (T-26, T-28).
- Keep the safety disclaimer visible in the app, README and demo.
- Log every completed task in `Log.md` with the commit hash.

**Assigned tasks:** see `To-Do.md` → "Member 1".

### Member 2 — Tech Lead & Delivery

| Field | Value |
|---|---|
| Name | `[fill in]` |
| GitHub handle | `[fill in]` |
| Contact | `[fill in]` |
| Role | Technical architect and delivery manager. Owns *how it works* and *whether we ship on time*. |
| Decision rights | Final say on architecture, thresholds and tuning, repository conventions, and the go/no-go for freeze. |

**Responsibilities**

- Maintain `Architecture.md`; build capture, perception, geometry, gesture engine, state machine, integration loop, logger and watchdog (T-03 to T-06, T-09 to T-12, T-19 to T-21).
- Own `To-Do.md`: update the Status column at every check-in, facilitate check-ins at H+2:00, H+4:00 and H+5:00 (R-03).
- Own repository hygiene: create the repo (T-01), run the mid-build commit audit at H+3:00 (R-05), and the final audit and tag (T-29).
- Tune thresholds and measure FPS and E-STOP latency (T-24, T-25).
- Run the fresh-clone dry run (T-27).
- Keep the safety logic (T-09 to T-12) protected: if time runs short, cut other work first.
- Log every completed task in `Log.md` with the commit hash.

**Assigned tasks:** see `To-Do.md` → "Member 2".

---

## 2. Responsibility Matrix (RACI)

R = Responsible (does it) · A = Accountable (final say) · C = Consulted · I = Informed

| Deliverable / activity | Member 1 | Member 2 |
|---|---|---|
| PRD, scope freeze, acceptance criteria | A / R | C |
| Design (wireframes, palette, HUD) | A / R | C |
| Architecture and tech decisions | C | A / R |
| Perception and gesture engine | C | A / R |
| Safety state machine | C | A / R |
| Simulated devices | A / R | C |
| Event log and KPI measurement | C | A / R |
| Gesture trials and idle test | R | R (observer) / A |
| README and demo script | A / R | C |
| Task board (`To-Do.md`) | I | A / R |
| `Log.md` upkeep | R (own tasks) | R (own tasks) / A |
| Repository hygiene, commit audits, final tag | C | A / R |
| Safety disclaimer present everywhere | A / R | C |

---

## 3. Working Agreements

### 3.1 Commit protocol (mandatory)

The event requires every change to be committed before making another move, and commit history is verified during evaluation.

1. **Clean-tree gate:** run `git status` before starting any new task. If it shows changes, commit them first.
2. **One logical change per commit.** If you cannot describe it in one line, split it.
3. **Message format:** `type(scope): summary` using these types:
   - `feat` new behaviour · `fix` bug fix · `docs` documentation · `test` tests · `refactor` no behaviour change · `chore` tooling, config · `tune` threshold changes (include before/after in the message body).
   - Examples: `feat(gestures): add open-palm and closed-fist classifier` · `tune(swipe): raise min speed 6 to 8 palm-widths/s` · `docs(log): add LOG-007 for T-09`.
4. **Never rewrite history:** no force-push, no `git rebase` or squash of shared commits, no `--amend` after pushing.
5. **Push at least every 30 minutes** and at every check-in, so the remote history is complete.
6. **Both of us pull before pushing** (`git pull`) and resolve conflicts with a normal merge commit.
7. **Log it:** add the commit hash to the matching `Log.md` entry.

Useful commands:

```bash
git status
git add -p                         # stage deliberately, not git add .
git commit -m "feat(safety): add RUNNING/PAUSED/ESTOP state machine"
git log --oneline -n 10
git push
```

### 3.2 Communication and cadence

| What | When | Who | Output |
|---|---|---|---|
| Kickoff and scope freeze | H+0:00 – 0:30 | Both | T-02 done; Must list agreed |
| Check-in 1 | H+2:00 | Member 2 facilitates | Status column updated; scope re-confirmed |
| Mid-build commit audit | H+3:00 | Member 2 | `git log --oneline` reviewed (R-05) |
| Check-in 2 | H+4:00 | Member 2 | Gate check against `To-Do.md` §3 |
| Check-in 3 | H+5:00 | Member 2 | Go/no-go on stretch items |
| Final audit | H+5:50 | Member 2 | Tag pushed (T-29) |

Check-ins are 10 minutes: what is done, what is next, what is blocked.

### 3.3 Decision rules

- **Product and UX decisions:** Member 1 decides after hearing Member 2.
- **Technical and threshold decisions:** Member 2 decides after hearing Member 1.
- **Disagreements:** timebox to 5 minutes, test it live if possible, decide, and record it in the decision log (`Log.md` §6).
- **Scope changes after H+0:30:** need both members to agree and a new `Log.md` decision row.

### 3.4 Definition of Done (per task)

- [ ] Meets the "Done when" column in `To-Do.md`
- [ ] Tests (if any) pass
- [ ] Committed with a clear message
- [ ] `Log.md` entry added with the commit hash
- [ ] Status column updated to `[x]`

### 3.5 Pairing and review

- Member 1 reviews all code that touches the HUD; Member 2 reviews anything that touches the state machine or thresholds.
- Safety logic (`safety.py`, hands-up detector) gets a second pair of eyes before it is merged into the integration loop.
- Review = read the diff and run the app once. Keep it under 10 minutes.

### 3.6 Escalation and wellbeing

- Blocked for more than 15 minutes: say so out loud and pair up.
- Falling behind a gate by more than 20 minutes: cut from Should and Could first (see `To-Do.md` §3).
- Take a short break around H+3:00. A tired demo is a risky demo.

---

## 4. Skill Matrix (fill in at kickoff)

Rate each skill 1 (new) to 5 (expert). Use it to rebalance tasks if someone is blocked or has spare capacity.

| Skill | Member 1 | Member 2 |
|---|---|---|
| Python | | |
| OpenCV | | |
| MediaPipe | | |
| NumPy / vector maths | | |
| Git and GitHub | | |
| UI / UX design | | |
| Testing (`pytest`) | | |
| Presenting / demoing | | |

---

## 5. Scaling the team (if more than 2 people join)

| New member | Suggested role | Takes over |
|---|---|---|
| Member 3 | QA and Documentation Lead | T-22, T-23 (trials and idle test), T-26 (README), S-05 (glove test) |
| Member 4 | Innovation / Stretch Lead | S-03 (calibration), S-04 (audio), S-07 (Gesture Recognizer comparison), S-06 (demo capture) |

When roles change, update this file, the RACI table and the **Assigned to** column in `To-Do.md`, and add a decision row in `Log.md` (commit each file change separately).
