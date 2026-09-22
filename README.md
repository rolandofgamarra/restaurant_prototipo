# restaurant

Sistema de gestión para restaurantes, lomiterías y hamburgueserías. Django + PostgreSQL.

Caja y cobros, comandas a cocina, inventario, compras y analítica, con acceso por roles y
operación garantizada aunque se caiga el internet del local.

**HelloWorld.py** · Rolando Fariña · Asunción, Paraguay

---

## Cómo se trabaja acá

Este repositorio no se toca a mano en el editor y después se le pide a un agente que
"arregle lo que falta". Se trabaja con un proceso, y el proceso está escrito:

| Archivo | Qué contiene |
|---|---|
| `docs/constitution.md` | Los 6 principios innegociables. Mandan sobre todo lo demás. |
| `AGENTS.md` | El contrato que cumple cualquier agente que entre al repo. |
| `docs/PIPELINE.md` | Las fases SDD, las compuertas G0-G6 y los bucles agénticos. |
| `docs/ARCHITECTURE.md` | La forma del sistema, para no deducirla leyendo código. |
| `docs/STATE.md` | Dónde está el proyecto ahora mismo. Se lee primero y se escribe último. |
| `docs/adr/` | Las decisiones tomadas, con la alternativa que se descartó y por qué. |
| `specs/` | Lo que hay que construir, en notación EARS. |

La regla que resume todas: **si no está en la spec, no se implementa; y nada está hecho
hasta que `make verify` esté en verde.**

## Arranque

```bash
uv sync --all-extras          # dependencias
cp .env.example .env          # y completar
make up                       # PostgreSQL + Redis
make install                  # hooks de pre-commit
```

El proyecto Django todavía no existe: se crea en la primera tarea del plan de la spec
001. Hasta entonces `make migrate` y `make verify` no tienen sobre qué correr, y eso es
deliberado — el código empieza después de la spec, no antes.

## Flujo de una funcionalidad

```bash
/sdd-spec  "cobro con pagos mixtos"   # entrevista y spec en EARS
/sdd-clarify                          # auditoría QA de la spec
/sdd-stack                            # 3 candidatos, evaluación, recomendación
/sdd-plan                             # plan técnico
/sdd-tasks                            # descomposición en tareas de <30 min
/sdd-build T1                         # una tarea, un commit, y para
/sdd-validate                         # veredicto RF por RF
/sdd-audit-privacy                    # auditoría de privacidad y seguridad
/sdd-handoff                          # despliegue documentado y spec archivada
```

Para cortar la sesión en cualquier punto sin perder el hilo: `/sdd-checkpoint`.

## Compuertas

```bash
make lint               # G0 formato y linting
make types              # G1 tipado estático
make test-unit          # G2 unitarios + cobertura ≥85% del dominio
make test-integration   # G3 integración contra PostgreSQL real
make migrations-check   # G4 migraciones
make security           # G5 bandit + pip-audit + check --deploy
make e2e                # G6 humo del flujo de caja

make verify             # G0..G5 — criterio de "tarea hecha"
make ship               # verify + G6 — criterio de "release"
make gates              # estado de cada compuerta, sin cortar al primer fallo
```

Las compuertas no se saltan, no se debilitan y no se silencian. Si una está mal, se
corrige la compuerta en su propio commit, con justificación.

## Estado

Fase 0 — spec 001 (caja y cobros) redactada, pendiente de clarificación y aprobación.
Ver `docs/STATE.md`.
