---
description: SDD phase 4 — run the build loop for exactly one task
argument-hint: "<task id, e.g. T3>"
---

Task: $ARGUMENTS

Run the build loop defined in `docs/PIPELINE.md` §2. Exactly one task. Then stop.

**1 · LOAD** — `docs/constitution.md`, `docs/STATE.md`, only the RF this task declares,
only the plan section for its module, only the files the plan names for it. If you need
a file the plan does not name, record that in STATE.md under `## Bloqueos` and stop.

**2 · RED** — dispatch `test-engineer`. Tests map 1:1 to the RF, named after them. Run
them: they must fail for the right reason. If one passes already, the test is wrong.

**3 · GREEN** — dispatch `django-implementer`. Minimum code to pass. Nothing else.

**4 · GATE** — `make verify`.

**5 · RETRY** — on red: diagnose the root cause, fix, re-run. Three attempts maximum.
On the fourth failure write the blocker into STATE.md (literal gate output, the three
hypotheses tested and why each was discarded, the decision you need from me) and stop.

**6 · REVIEW** — dispatch `code-reviewer` on `git diff`. If the task touched
`*/migrations/`, also dispatch `migration-reviewer`. Blocking findings go back to step 3
and count against the same budget of three.

**7 · CHECKPOINT** — tick the task in `tasks.md`, update `docs/STATE.md`, one atomic
commit: `<type>(scope): <description> [Tn, RF-a, RF-b]`.

**8 · STOP** — do not start the next task. Report: what was built, which RF are now
covered, gate status, and what is next.
