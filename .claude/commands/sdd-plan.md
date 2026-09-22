---
description: SDD phase 2 — technical plan for the approved spec
---

Refuse to run unless all four inputs exist and are approved: `docs/constitution.md`,
`docs/ARCHITECTURE.md`, the active `spec.md`, the active `stack.md`.

Dispatch the `architect` subagent. Write no production code.

Produce `specs/NNN/plan.md` with:

1. Module structure — file by file, each annotated with the RF it covers
2. Data model — Django field types, indexes, constraints, example row
3. Pseudocode for every non-obvious algorithm
4. Technical decisions, each with the discarded alternative and why
5. Test strategy, including what gets injected for determinism (the clock above all)
6. **Declared file list per task area** — the build loop reads only what you name here
7. RF coverage table; an uncovered RF blocks approval

Update `docs/STATE.md` and stop for approval.
