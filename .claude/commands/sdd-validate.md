---
description: SDD phase 5 — verdict on whether the spec is actually fulfilled
---

Walk the active `spec.md` **requirement by requirement**, RF-1 to the last one.

For each: name the test that covers it, run that test, and report the literal result.
If a requirement has no test, or its test fails, say so plainly — do not soften it.

Then check every line of the spec's "Criterios de finalización".

Write `specs/NNN/validation.md` in Spanish containing:

```
RF-n | test | resultado | veredicto
```

followed by a final verdict: **¿la spec está cumplida? sí / no**, and if no, the exact
list of what is missing.

Run `make ship` (verify + E2E) and include its output.

Do not fix anything in this command. Detecting and fixing in the same pass is how a
validation becomes a rubber stamp.
