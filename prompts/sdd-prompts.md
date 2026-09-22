# Biblioteca de prompts por fase

Los comandos `/sdd-*` ya encapsulan esto. Esta tabla existe para cuando trabajes fuera de
Claude Code (opencode, Cursor, ChatGPT) o quieras ajustar un prompt a mano.

| Fase | Prompt |
|---|---|
| **Constitución** | "Proponeme la constitución de este proyecto: 6 principios innegociables, cortos y verificables, sobre disponibilidad, relación spec-código, inmutabilidad del historial, separación de capas y funciones, seguridad por diseño y criterio de 'hecho'. Máximo 15 líneas. Esperá mi aprobación." |
| **Spec** | "NO escribas código en ningún momento. Hacéme preguntas de UNA en UNA, máximo 6, sobre casos límite, comportamiento ante errores y qué queda fuera del alcance. Con mis respuestas generá `specs/NNN/spec.md` con RF numerados en EARS, fuera de alcance y criterios de finalización. Solo el QUÉ y el POR QUÉ: nada de stack, arquitectura ni nombres de archivo." |
| **Clarificación** | "Revisá la spec como un QA muy exigente. Listá, numerado, en cuatro bloques: (1) ambigüedades, (2) contradicciones entre requisitos, (3) casos límite no cubiertos, (4) conflictos con la constitución. Solo detectá: no propongas soluciones todavía." |
| **Stack** | "Proponé tres stacks candidatos reales para lo que esta feature introduce. Evaluá cada uno por encaje con el negocio, seguridad por diseño y por defecto, escalabilidad, operabilidad, encaje con el equipo y reversibilidad. Recomendá uno y decime cuál descartaste y por qué. Escribí `stack.md` y esperá aprobación." |
| **Plan** | "Leé la constitución, la spec y el stack. NO escribas código. Generá `plan.md` con: estructura de módulos anotada por RF, modelo de datos con tipos Django concretos y una fila de ejemplo, pseudocódigo de cada algoritmo no obvio, decisiones técnicas con la alternativa descartada, estrategia de tests, lista de archivos declarados por tarea y tabla de cobertura de RF." |
| **Tareas** | "A partir de la spec y el plan, generá `tasks.md`: tareas de menos de 30 minutos, ordenadas por dependencia, cada una con los RF que cubre, los archivos exactos que toca y una línea 'Hecho cuando:' verificable. Con checkboxes. Si el contexto de una tarea no entra cómodo en una sesión nueva, partila." |
| **Construcción** | "Implementá SOLO la tarea Tn. Escribí primero los tests que fallan, después el código mínimo. Corré `make verify` y mostráme el resultado. Máximo 3 intentos de corrección; al cuarto fallo anotá el bloqueo en STATE.md y pará. Al terminar: marcá Tn, actualizá STATE.md, un commit, y PARÁ. No empieces Tn+1." |
| **Validación** | "Recorré la spec requisito por requisito. Para cada RF: qué test lo cubre y el resultado de ejecutarlo. Después verificá los criterios de finalización. Veredicto final: ¿la spec está cumplida? No arregles nada en esta pasada." |
| **Auditoría** | "Auditá esta feature: inventario y minimización de datos, mínimo privilegio entre roles, integridad del log de auditoría, superficie de ataque, caminos de fraude propios de un POS, secretos y configuración, dependencias vulnerables. Ordená por severidad, cada hallazgo con el escenario concreto que lo explota. Sin inflar severidades." |
| **Cambio** | "Nuevo requisito: <X>. NO toques el código. Actualizá primero la spec (nuevo RF en EARS + casos límite) y mostráme el diff de la spec." |
| **Checkpoint** | "Escribí STATE.md para que una sesión nueva pueda retomar leyendo solo eso. Resumí el estado del repositorio, no la conversación. Después corré `make verify` y decime en qué color quedamos." |

## Reglas que valen para cualquier prompt

- Si no está en la spec, no se implementa.
- Un hueco marcado `[NECESITA ACLARACIÓN]` bloquea la fase siguiente.
- Ninguna tarea se cierra sin `make verify` en verde.
- Una tarea por sesión. Después del commit, parar.
- Si no estás seguro de un dato de SIFEN, DNIT o Bancard, no lo escribas: marcalo.
