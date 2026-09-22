# PIPELINE.md — fases, compuertas y bucles agénticos

Este documento define **cómo se trabaja**, no qué se construye. Es la pieza que convierte
"un agente que escribe código" en un proceso de ingeniería repetible.

## Principio rector

> Un bucle agéntico solo puede cerrarse con una señal **verificable por máquina**.
> Nunca con el juicio del modelo sobre su propio trabajo.

De ahí se derivan las tres reglas que sostienen todo lo demás:

1. **Terminación objetiva.** El criterio de "hecho" es `make verify` en verde, no una
   afirmación del agente.
2. **Presupuesto de intentos.** Tres correcciones. A la cuarta falla, el bucle escala a
   un humano. Un bucle de auto-corrección sin tope quema tokens y no converge.
3. **Progreso persistido en disco.** Checkboxes en `tasks.md` y estado en `STATE.md`.
   El contexto es volátil; el disco no.

---

## 1. Bucle externo — flujo SDD (con humano en la compuerta)

Cada fase produce un artefacto y **espera aprobación explícita** antes de avanzar.
Un agente nunca cruza una fase por su cuenta.

| # | Fase | Comando | Artefacto | Aprueba |
|---|---|---|---|---|
| -1 | Constitución | — | `docs/constitution.md` | Humano (una vez) |
| 0 | Especificación | `/sdd-spec` | `specs/NNN/spec.md` | Humano |
| 0.5 | Clarificación | `/sdd-clarify` | hallazgos → spec corregida | Humano |
| 1 | Selección de stack | `/sdd-stack` | `specs/NNN/stack.md` | Humano |
| 2 | Plan técnico | `/sdd-plan` | `specs/NNN/plan.md` | Humano |
| 3 | Descomposición | `/sdd-tasks` | `specs/NNN/tasks.md` | Humano |
| 4 | Construcción | `/sdd-build Tn` | código + tests + commit | Compuertas |
| 5 | Validación | `/sdd-validate` | `specs/NNN/validation.md` | Humano |
| 6 | Auditoría privacidad | `/sdd-audit-privacy` | `specs/NNN/privacy-audit.md` | Humano |
| 7 | Handoff | `/sdd-handoff` | `specs/done/NNN/` + DEPLOYMENT | Humano |

Reglas del bucle externo:

- **Sin spec aprobada no hay stack.** Sin stack aprobado no hay plan. Sin plan aprobado
  no hay tareas. Sin tareas no hay código. La secuencia no se negocia.
- **Un cambio de requisito entra por la spec.** Nuevo requisito a mitad de camino: se
  actualiza `spec.md` primero, se muestra el diff, se re-corre clarificación sobre lo
  nuevo, y recién después se toca el plan. Jamás directo al código.
- **Un `[NECESITA ACLARACIÓN]` bloquea la fase siguiente.** El hueco visible es
  información; la suposición silenciosa es deuda.

---

## 2. Bucle interno — construcción de una tarea

Es el bucle que se ejecuta decenas de veces. Cada iteración produce **un commit atómico**.

```
ENTRADA: Tn (una tarea de tasks.md, ≤30 min de trabajo humano equivalente)

1. LOAD
     docs/constitution.md
     docs/STATE.md
     specs/NNN/spec.md        -> solo los RF que Tn declara cubrir
     specs/NNN/plan.md        -> solo el módulo que Tn toca
     los archivos que plan.md nombra para Tn, y ninguno más
   Si necesitás abrir un archivo que el plan no nombra, el plan está incompleto:
   anotalo en STATE.md y pará.

2. RED
     Escribir el/los test(s) que fallan, mapeados 1:1 con los RF de Tn.
     Ejecutar. DEBE fallar por la razón correcta.
     Si pasa a la primera -> el test no prueba nada. Corregir el test antes de seguir.

3. GREEN
     Escribir el mínimo código que hace pasar el test. Nada más.
     Prohibido: refactors oportunistas, "mejoras" no pedidas, archivos no declarados.

4. GATE
     make verify        (G0..G5)

5. RETRY  (si la compuerta está roja)
     intento += 1
     intento <= 3 -> diagnosticar la causa raíz, corregir, volver a 4
     intento  > 3 -> escribir en STATE.md ## Bloqueos:
                       - qué falla, salida literal de la compuerta
                       - las 3 hipótesis probadas y por qué se descartaron
                       - la decisión concreta que se necesita
                     y PARAR.

6. REVIEW
     Despachar el subagente `code-reviewer` sobre `git diff`.
     Hallazgo bloqueante -> volver a 3 (cuenta contra el mismo presupuesto de 3).
     El subagente consume su propio contexto y devuelve solo el veredicto.

7. CHECKPOINT
     - marcar Tn en tasks.md con [x]
     - actualizar docs/STATE.md (fase, tarea, último commit, bloqueos, deuda)
     - un commit: feat(scope): descripción [Tn, RF-a, RF-b]

8. STOP
     No empezar Tn+1. Devolver el control.
```

**Por qué el paso 8 es obligatorio.** Encadenar tareas dentro de una misma sesión es lo
que produce la pérdida de contexto que obliga a compactar. Una tarea = una sesión = un
commit = una unidad revisable. Es más lento por iteración y mucho más rápido por proyecto.

---

## 3. Compuertas G0–G6

Todas ejecutables. Todas cableadas en el `Makefile`, en `pre-commit` y en CI. Un agente
y un humano corren exactamente lo mismo.

| Compuerta | Comando | Qué bloquea |
|---|---|---|
| G0 Estilo | `make lint` | `ruff format --check` + `ruff check` |
| G1 Tipos | `make types` | `mypy`, estricto en `src/domain` y `src/*/services` |
| G2 Unitarios | `make test-unit` | pytest unit, cobertura ≥ 85% en dominio y servicios |
| G3 Integración | `make test-integration` | pytest contra PostgreSQL real |
| G4 Migraciones | `make migrations-check` | migración faltante, o destructiva sin ADR |
| G5 Seguridad | `make security` | `bandit`, `pip-audit`, `django check --deploy` |
| G6 E2E | `make e2e` | humo del flujo de caja completo (solo antes de release) |

```
make verify  = G0 G1 G2 G3 G4 G5      <- criterio de "tarea hecha"
make ship    = verify + G6            <- criterio de "release"
```

**G4 merece una nota.** Una migración de Django puede bloquear una tabla de ventas en
plena hora pico o borrar una columna con datos. Toda migración pasa por el subagente
`migration-reviewer` antes del commit: verifica reversibilidad, ausencia de operaciones
destructivas sin respaldo, y que no tome locks largos sobre tablas calientes.

**Cobertura.** El 85% se mide sobre `src/domain` y `src/*/services`, no sobre el
proyecto entero. Cubrir `settings.py` no prueba nada; cubrir el cálculo de vuelto sí.

---

## 4. Elenco de agentes

Cada uno tiene su archivo en `.claude/agents/`. El modelo se asigna por carga de
razonamiento, no por importancia.

| Agente | Fase | Modelo | Función |
|---|---|---|---|
| `sdd-spec-writer` | 0, 0.5 | Opus | Entrevista de a una pregunta, redacta EARS, audita specs |
| `stack-advisor` | 1 | Opus | Tres candidatos, evaluación, recomendación segura y escalable |
| `architect` | 2 | Opus | Plan técnico, modelo de datos, decisiones con alternativa descartada |
| `django-implementer` | 4 | Sonnet | Escribe el código de la tarea. Solo la tarea |
| `test-engineer` | 4 | Sonnet | Tests que fallan primero, mapeados a RF |
| `code-reviewer` | 4 | Opus | Revisa el diff. Veredicto bloqueante o no bloqueante |
| `migration-reviewer` | 4 (G4) | Opus | Seguridad y reversibilidad de migraciones |
| `security-auditor` | 6 | Opus | Privacidad por diseño, superficie de ataque, datos sensibles |

Regla de despacho: los agentes de **lectura masiva** (reviewer, auditor, architect en
fase de exploración) se despachan siempre como subagentes. Queman su propio contexto y
devuelven un veredicto corto. Eso es lo que mantiene viva la sesión principal.

---

## 5. Economía de contexto

Presupuesto orientativo por sesión de construcción:

- constitución + STATE.md + AGENTS.md: ~4k tokens (fijo, siempre)
- RF de la tarea + sección del plan: ~2k
- archivos declarados por la tarea: ~10k
- trabajo: el resto

Si una tarea no entra en ese presupuesto, la tarea es demasiado grande. Volver a
`/sdd-tasks` y partirla. Esto no es una limitación técnica que se tolera: es la señal de
que la descomposición estaba mal hecha.

Prohibiciones que sostienen el presupuesto:

- No `grep` sobre todo el repo "para entender el contexto". El plan es el contexto.
- No leer archivos "por las dudas".
- No pegar contenido de archivos en el chat. Referenciar `ruta:línea`.
- No dejar que el agente descubra la arquitectura leyendo código. Está en `ARCHITECTURE.md`.

---

## 6. Flujo diario en VS Code

```bash
# arranque de sesión
make up                     # postgres + redis
git pull && make install

# fase de diseño (una vez por feature)
/sdd-spec  "cobro con pagos mixtos"
/sdd-clarify
/sdd-stack
/sdd-plan
/sdd-tasks

# fase de construcción (una vez por tarea)
/sdd-build T1
# ...revisar el diff, aprobar el commit...
/sdd-build T2

# cierre de feature
/sdd-validate
/sdd-audit-privacy
/sdd-handoff
```

Si en cualquier punto hay que cortar: `/sdd-checkpoint` escribe STATE.md y deja la
sesión en un punto del que se puede retomar mañana sin releer nada.
