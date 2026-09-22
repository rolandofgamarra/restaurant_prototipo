---
description: SDD phase 3 — decompose the plan into small dependency-ordered tasks
---

From the approved `spec.md` and `plan.md`, write `specs/NNN/tasks.md`.

Rules for each task:

- Small enough to finish in roughly 30 minutes of equivalent human work
- Ordered by dependency, numbered `T1`, `T2`, …
- Declares the RF it covers
- Declares the exact files it touches (taken from the plan's declared file list)
- Has one `Hecho cuando:` line that is objectively verifiable — a passing test, not an
  opinion
- Rendered as a checkbox: `- [ ] T1 — …`

Sanity check before you finish: if a task's context (constitution + its RF + its plan
section + its declared files) would not comfortably fit in a fresh session, the task is
too big. Split it. That check is the whole point of this phase.

Update `docs/STATE.md` and stop for approval.
