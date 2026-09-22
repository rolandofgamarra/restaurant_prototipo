---
description: Persist session state so work can resume tomorrow without re-reading anything
---

Write `docs/STATE.md` so that a fresh session can resume from it alone. Keep it under
60 lines, in the existing format:

- Fecha, fase SDD, spec activa, tarea en curso, último commit
- Hecho — solo lo cerrado y verificado, no lo que está a medias
- Siguiente — los próximos pasos concretos, en orden
- Decisiones vigentes — resumen; el detalle vive en los ADR
- Bloqueos — qué falla, qué se probó, qué decisión se necesita de mí
- Deuda conocida

Then run `make verify` and report the gate status, so the next session knows whether it
is starting from green or from red.

Do not summarise the conversation. Summarise the **state of the repository**. The next
session does not need to know what we discussed; it needs to know where the code is.
