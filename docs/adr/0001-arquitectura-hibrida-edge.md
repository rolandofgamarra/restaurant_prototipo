# ADR 0001 — Arquitectura híbrida con servidor local (edge)

**Estado:** aceptada
**Fecha:** 2026-09-22 (aprobada por Rolando el 2026-09-22)

## Contexto

El restaurante opera en Paraguay con conectividad no garantizada. El requisito de negocio
es explícito: si falla el router o el proveedor de internet, el local tiene que seguir
operando y cobrando.

"La app deja de funcionar" no es una falla sino cinco, y cada una tiene consecuencias
distintas: cae el ISP, cae el router (LAN), cae el servidor, se rompe el equipo de caja,
o cae un tercero (POS de tarjetas, pasarela QR, SIFEN).

## Decisión

Servidor local (edge) dentro del restaurante — un mini PC corriendo Django, PostgreSQL y
Redis — como fuente de verdad durante la operación. Todas las terminales (cajas, pantalla
de cocina, celulares de mozos) hablan con él por LAN. La nube es réplica, analítica,
respaldo y acceso remoto del administrador.

Internet se necesita únicamente para sincronizar, para cobros con tarjeta y QR, y más
adelante para SIFEN.

Se definen cinco niveles de degradación (N0 a N4, ver `ARCHITECTURE.md` §2) y el nivel
activo se muestra permanentemente en la interfaz de caja.

## Alternativas descartadas

**Nube pura con PWA offline en la caja.** Más barata en infraestructura y bastante más
cara en complejidad. Sin LAN, las terminales tampoco se ven entre sí: la comanda no llega
a la cocina y la operación vuelve al papel. Sirve para una sola caja y no escala a un
salón. Descartada.

**Aplicación de escritorio local sin nube.** Resuelve la disponibilidad y pierde el
acceso remoto del administrador, la analítica consolidada y el respaldo fuera del local
— que es justamente donde el dueño obtiene valor. Descartada.

## Consecuencias

- Aparece hardware que hay que comprar, instalar y mantener en cada cliente.
- Aparece un módulo de sincronización con reconciliación, que es trabajo real y no trivial.
- El modelo de datos queda condicionado por el ADR 0003 (UUID e historial append-only).
- A cambio: el local opera al 100% sin internet, que es el requisito que originó el proyecto.
- Mitigación de la falla de router: router de repuesto preconfigurado en el local y la
  caja principal cableada por Ethernet directo al edge box.

## Deuda de despliegue

Decisiones operativas/comerciales que no condicionan el modelo del sistema ni la spec
001; quedan abiertas explícitamente, no bloquean esta aprobación, y se resuelven en la
fase de handoff (`docs/DEPLOYMENT.md`):

- Modelo de hardware y su costo por instalación.
- Quién mantiene físicamente el equipo en el local del cliente.
