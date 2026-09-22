---
description: SDD phase 0.5 — audit the active spec as a QA professional
---

Dispatch the `sdd-spec-writer` subagent in audit mode against the active spec named in
`docs/STATE.md`.

Review it as a very demanding QA engineer. Detect only — propose no solutions yet.

Return a numbered list in exactly four blocks:

1. Ambigüedades restantes
2. Contradicciones entre requisitos
3. Casos límite no cubiertos
4. Conflictos con la constitución

Then tell me how many `[NECESITA ACLARACIÓN]` markers remain. While any remain, the
next phase is blocked.
