# STATE.md — estado vivo del proyecto

> Lo primero que lee un agente y lo último que escribe. Máximo 60 líneas.
> Si la sesión muere, la siguiente debe poder retomar leyendo solo este archivo.

**Actualizado:** 2026-09-22
**Fase SDD:** 3 completa — `tasks.md` aprobado (T1-T83). Lista para entrar al bucle de
construcción.
**Spec activa:** `specs/001-caja-y-cobros/` (spec.md 39 RF, plan.md, tasks.md — los tres
aprobados)
**Tarea en curso:** ninguna. Próxima a tomar: **T1** (ver `tasks.md`).
**Último commit:** —

## Hecho

- Constitución, ADR 0001-0004 aceptados (0004 incluye cláusula de auto-autorización).
- Spec 001 redactada, clarificada y **aprobada**, 39 RF. RF-17..RF-21: comprobante por
  correo (no impresión) — SIFEN/factura formal queda fuera, en spec futura sin número
  aún, que exige leer `docs/dumentacion_SIFEN/` antes de escribirse.
- `stack.md` **aprobado**: proveedor transaccional de email vía API (SES inicial) detrás
  de `notifications/providers/base.py`, disparado por Celery.
- `plan.md` **aprobado**: apps `cash/`, `orders/` (Venta y LineaVenta), `payments/`,
  `accounts/` (autorización PIN), `audit/`, `sync/`, app nueva `notifications/`.
  Supuestos S1 (snapshot de producto sin `catalog`), S2 (RF-39 solo puerto no-bloqueante
  sin `inventory` real) y S3 (`notifications/` nueva) confirmados por Rolando.
  `docs/ARCHITECTURE.md` §3 actualizado con `notifications/`.
- `tasks.md` **aprobado**: 83 tareas (T1-T83), 39/39 RF cubiertos, orden de dependencia
  real, cada una con archivos exactos y "Hecho cuando" verificable. 3
  `[NECESITA ACLARACIÓN]` de bajo riesgo aceptadas tal como quedaron (helpers `shared/`
  sin test propio, `accounts/admin.py` sin RF, tres rutas de test fuera de la lista §6
  del plan pero coherentes con otras secciones).

## Siguiente

1. Entrar al bucle de construcción (`AGENTS.md` §4) empezando por **T1**.
2. Cuando el negocio esté listo: redactar spec dedicada de facturación SIFEN, leyendo
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
- Bancard sin documentación — no se escribe ese módulo sin el PDF oficial. SIFEN sí
  tiene documentación (`docs/dumentacion_SIFEN/`), pero no fue leída/analizada aún.
- Spec 001 captura email del cliente (RF-17/18): PII nueva. `docs/PRIVACY.md` necesita
  actualizarse en `/sdd-audit-privacy` antes de cerrar la spec 001.
- Doble anulación, dos terminales sobre la misma mesa, redondeo de descuentos
  porcentuales: casos límite listados en spec 001 sin RF dedicado — revisar si alguna
  tarea de `tasks.md` los cubre implícitamente o si hace falta ampliar la spec después.
