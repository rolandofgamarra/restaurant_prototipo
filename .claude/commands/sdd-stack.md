---
description: SDD phase 1 — evaluate three candidate stacks and recommend one
---

Refuse to run if the active spec still contains `[NECESITA ACLARACIÓN]` markers or has
not been approved.

Dispatch the `stack-advisor` subagent.

Propose three genuine candidates for whatever this feature actually introduces. Do not
default to the incumbent and do not include a straw man. Evaluate on business fit,
security by design and by default, scalability, operability, team fit and reversibility.

Recommend one, and state the discarded alternative and why. List the constraints the
choice imposes on the plan.

Remember the foundations already fixed by ADR and not open here: Django + PostgreSQL,
single-tenant, hybrid edge topology, integer Guaraní, UUID PKs, append-only history,
third parties behind an owned interface.

Write `specs/NNN/stack.md` in Spanish, update `docs/STATE.md`, and stop for approval.
