# STATE.md — estado vivo del proyecto

> Lo primero que lee un agente y lo último que escribe. Máximo 60 líneas.
> Si la sesión muere, la siguiente debe poder retomar leyendo solo este archivo.

**Actualizado:** 2026-09-22
**Fase SDD:** 4 — Build loop. **T1, T2, T3, T5 hechas** (T5 adelantada fuera de orden).
`make verify` (G0-G5) en verde, 100% cobertura en `shared/`.
**Spec activa:** `specs/001-caja-y-cobros/` (spec.md 39 RF, plan.md, tasks.md aprobados,
84 tareas T1-T84)
**Tarea en curso:** ninguna. Próxima a tomar: **T4** (reloj inyectable, `shared/clock.py`).
**Último commit:** ver `git log` (T3 se commitea junto con esta actualización)

## Hecho

- Constitución, ADR 0001-0004 aceptados. Spec 001 aprobada, 39 RF (RF-17..RF-21:
  comprobante por correo; SIFEN queda para spec futura). `stack.md` aprobado (email vía
  SES, interfaz propia). `plan.md` aprobado (apps `cash/orders/payments/accounts/audit/
  sync/notifications`, supuestos S1-S3 confirmados). `tasks.md` aprobado, 84 tareas.
- `docs/documentacion_SIFEN/` **leída completa**, guardada en memoria persistente del
  proyecto ("SIFEN — Manual Técnico", "SIFEN — próximo paso"). No alcanza para escribir
  la spec: 5 vacíos bloqueantes (contingencia no definida en v150 es el más grave) y
  "numeración por terminal" no respaldada por el MT (unidad fiscal = punto de expedición
  autorizado por SGTM, no la terminal). Ver "Deuda conocida" y la memoria para el detalle.
- **T1 hecha** (esqueleto Django). Entorno: `uv`+Docker Desktop+`docker compose up -d`,
  `.env` local (gitignorado, `DJANGO_LAN_SIN_TLS=True`). `DATABASE_URL` obligatoria. G5
  fuerza `DJANGO_DEBUG=False DJANGO_LAN_SIN_TLS=False`. `ruff` excluye
  `specs|docs|prompts/**/*.md`. `make` no existe en esta shell git-bash — `uv run ...`.
- **T2 hecha** (`redondear_gs`, `shared/money.py`, 8 tests, 100% cobertura).
- **T5 hecha, adelantada fuera de orden.** `ErrorDeNegocio(Exception)` con
  código+mensaje, coexiste con `Resultado[T]` (`Ok`/`Error`, PEP 695).
- **T3 hecha** (`cuadrar_lineas`, RF-15, 17 tests, 100% cobertura sobre `shared/`).

## Siguiente

1. T4 — reloj inyectable (`shared/clock.py`, RF-1/RF-33/RF-38).
2. Continuar el bucle T6, T7, ... (T5 ya hecha; ver `tasks.md`).
3. Facturación SIFEN: antes de redactar esa spec, conseguir lo que falta (ver memoria
   "SIFEN — próximo paso": PDF del dígito verificador, Notas Técnicas posteriores a
   v150, XSD oficiales, guía de habilitación) — nunca inventar detalles (no-negociable).

## Decisiones vigentes (resumen — el detalle está en los ADR)

- Django + PostgreSQL, single-tenant; servidor local (edge) + réplica nube; N0-N4
- Guaraníes enteros, redondeo en `shared/money.py`; UUID PK; numeración por terminal
- SIFEN fuera del alcance inicial; Bancard declarado por el cajero, sin integración directa
- Roles: cajero, supervisor, administrador, mozo + superusuario técnico

## Bloqueos

- Ninguno.

## Deuda conocida

- `docs/DEPLOYMENT.md` esqueleto (handoff). Bancard sin documentación — no escribir
  código de esa integración. SIFEN: documentación leída pero incompleta (ver "Hecho").
- Spec 001 captura email del cliente (RF-17/18): PII nueva, `docs/PRIVACY.md` necesita
  actualizarse en `/sdd-audit-privacy` antes de cerrar la spec.
- Doble anulación, dos terminales sobre la misma mesa, redondeo de descuentos
  porcentuales: casos límite sin RF dedicado — revisar si `tasks.md` los cubre.
