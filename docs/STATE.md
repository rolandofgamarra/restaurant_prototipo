# STATE.md — estado vivo del proyecto

> Lo primero que lee un agente y lo último que escribe. Máximo 60 líneas.
> Si la sesión muere, la siguiente debe poder retomar leyendo solo este archivo.

**Actualizado:** 2026-09-22
**Fase SDD:** 4 — Build loop. **T1 hecha.** Entrando a T2 en la misma sesión (test RED ya
escrito) para no dejar el repo con `pytest --collect-only` en rojo entre tareas.
**Spec activa:** `specs/001-caja-y-cobros/` (spec.md 39 RF, plan.md, tasks.md aprobados,
84 tareas T1-T84)
**Tarea en curso:** T2 — redondeo en `src/shared/money.py`, test RED ya existe.
**Último commit:** ver `git log` (T1 se commitea junto con esta actualización)

## Hecho

- Constitución, ADR 0001-0004 aceptados. Spec 001 aprobada, 39 RF (RF-17..RF-21:
  comprobante por correo; SIFEN queda para spec futura, requiere leer
  `docs/dumentacion_SIFEN/` antes de escribirse). `stack.md` aprobado (email vía SES,
  interfaz propia). `plan.md` aprobado (apps `cash/orders/payments/accounts/audit/sync/
  notifications`, supuestos S1-S3 confirmados). `tasks.md` aprobado, 84 tareas.
- **T1 (esqueleto Django) hecha.** Entorno: `uv` en `~/.local/bin`, `uv sync
  --all-extras` corrido, Docker Desktop + `docker compose up -d` (Postgres/Redis)
  corriendo, `.env` local creado desde `.env.example` (gitignorado,
  `DJANGO_LAN_SIN_TLS=True` para dev sin TLS). `DATABASE_URL` sin default hardcodeado:
  sin `.env`, falla fuerte. G5 (`check --deploy`) fuerza `DJANGO_DEBUG=False
  DJANGO_LAN_SIN_TLS=False` en el `Makefile` para no depender del `.env` del
  desarrollador. `ruff` excluye `specs|docs|prompts/**/*.md` (formatea código embebido
  por defecto). `make` no existe en esta shell git-bash — usar `uv run ...` directo.

## Siguiente

1. T2 — redondeo en `src/shared/money.py` (test RED ya escrito).
2. Continuar el bucle T3, T4, ... (ver `tasks.md`).
3. Cuando el negocio esté listo: redactar spec dedicada de facturación SIFEN, leyendo
   `docs/dumentacion_SIFEN/` primero — nunca inventar detalles de SIFEN (no-negociable).

## Decisiones vigentes (resumen — el detalle está en los ADR)

- Django + PostgreSQL, single-tenant; servidor local (edge) + réplica nube; N0-N4
- Guaraníes enteros, redondeo en `shared/money.py`; UUID PK; numeración por terminal
- SIFEN fuera del alcance inicial; Bancard declarado por el cajero, sin integración directa
- Roles: cajero, supervisor, administrador, mozo + superusuario técnico

## Bloqueos

- Ninguno.

## Deuda conocida

- `docs/DEPLOYMENT.md` esqueleto: se completa en handoff de spec 001.
- Bancard sin documentación. SIFEN tiene documentación (`docs/dumentacion_SIFEN/`) pero
  no fue leída/analizada aún — no escribir código de esa integración sin leerla primero.
- Spec 001 captura email del cliente (RF-17/18): PII nueva, `docs/PRIVACY.md` necesita
  actualizarse en `/sdd-audit-privacy` antes de cerrar la spec.
- Doble anulación, dos terminales sobre la misma mesa, redondeo de descuentos
  porcentuales: casos límite sin RF dedicado — revisar si `tasks.md` los cubre.
