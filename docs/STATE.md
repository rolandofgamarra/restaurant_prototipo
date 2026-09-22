# STATE.md — estado vivo del proyecto

> Lo primero que lee un agente y lo último que escribe. Máximo 60 líneas.
> Si la sesión muere, la siguiente debe poder retomar leyendo solo este archivo.

**Actualizado:** 2026-09-22
**Fase SDD:** 4 — Build loop. **T1, T2, T5 hechas** (T5 adelantada fuera de orden a
pedido de Rolando, para usarla en T3). `make verify` (G0-G5) en verde.
**Spec activa:** `specs/001-caja-y-cobros/` (spec.md 39 RF, plan.md, tasks.md aprobados,
84 tareas T1-T84)
**Tarea en curso:** T3 — cuadre de líneas (`shared/money.py`), test RED ya escrito,
retomando el GREEN ahora con `ErrorDeNegocio` disponible.
**Último commit:** ver `git log` (T5 se commitea junto con esta actualización)

## Hecho

- Constitución, ADR 0001-0004 aceptados. Spec 001 aprobada, 39 RF (RF-17..RF-21:
  comprobante por correo; SIFEN queda para spec futura, requiere leer
  `docs/dumentacion_SIFEN/` antes de escribirse). `stack.md` aprobado (email vía SES,
  interfaz propia). `plan.md` aprobado (apps `cash/orders/payments/accounts/audit/sync/
  notifications`, supuestos S1-S3 confirmados). `tasks.md` aprobado, 84 tareas.
- **T1 hecha** (esqueleto Django). Entorno: `uv` en `~/.local/bin`, Docker Desktop +
  `docker compose up -d`, `.env` local desde `.env.example` (gitignorado,
  `DJANGO_LAN_SIN_TLS=True`). `DATABASE_URL` obligatoria (falla fuerte sin `.env`). G5
  fuerza `DJANGO_DEBUG=False DJANGO_LAN_SIN_TLS=False` en el `Makefile`. `ruff` excluye
  `specs|docs|prompts/**/*.md`. Plugin `pydantic.mypy` habilitado. `make` no existe en
  esta shell git-bash — usar `uv run ...` directo.
- **T2 hecha** (`redondear_gs`). `src/shared/money.py`, 8 tests, 100% cobertura.
- **T5 hecha, adelantada fuera de orden** (a pedido de Rolando: el RED de T3 necesitaba
  decidir si `cuadrar_lineas` lanza excepción). `ErrorDeNegocio(Exception)` con
  código+mensaje, coexiste con `Resultado[T]` (`Ok`/`Error`, PEP 695). Corrigió una
  contradicción real en `plan.md` §1.2 vs §3.3/§3.4 sobre si se lanzan excepciones.

## Siguiente

1. T3 — retomar GREEN de `cuadrar_lineas` en `shared/money.py` (RF-15), usando
   `ErrorDeNegocio` para el caso de línea negativa.
2. Continuar el bucle T4, T6, T7, ... (T5 ya hecha; ver `tasks.md`).
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

- `docs/DEPLOYMENT.md` esqueleto (handoff). Bancard sin documentación; SIFEN sí tiene
  (`docs/dumentacion_SIFEN/`) pero no leída — no escribir código de esas integraciones.
- Spec 001 captura email del cliente (RF-17/18): PII nueva, `docs/PRIVACY.md` necesita
  actualizarse en `/sdd-audit-privacy` antes de cerrar la spec.
- Doble anulación, dos terminales sobre la misma mesa, redondeo de descuentos
  porcentuales: casos límite sin RF dedicado — revisar si `tasks.md` los cubre.
