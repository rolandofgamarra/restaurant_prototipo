# ADR 0003 — Identidad UUID, numeración por terminal e historial append-only

**Estado:** aceptada
**Fecha:** 2026-09-22

## Contexto

El ADR 0001 admite operación offline en varias terminales simultáneamente. Dos cajas sin
conexión generando registros con claves autoincrementales producen colisiones, y la
reconciliación se vuelve imposible. En paralelo, el negocio exige un panel de auditoría
por roles capaz de responder quién anuló qué y cuándo.

Estos dos problemas tienen una sola solución estructural, y conviene verlo antes de
escribir el primer modelo: **ninguno de los dos se puede agregar después sin migrar
datos de producción.**

## Decisión

1. **`UUIDField` como clave primaria** en toda entidad creable offline: venta, línea de
   venta, pago, comanda, movimiento de stock, evento de auditoría, sesión de caja. Las
   claves autoincrementales quedan prohibidas en esas tablas.
2. **Numeración de comprobantes por terminal**, no global: establecimiento + punto de
   expedición + secuencia local. Coincide con lo que SIFEN exige y evita una migración
   dolorosa más adelante.
3. **Historial append-only.** Ventas, pagos y movimientos de stock son eventos inmutables.
   Una anulación es un evento nuevo que referencia al original. Prohibidos `DELETE` y
   `UPDATE` destructivo sobre esas tablas, con la prohibición implementada a nivel de
   modelo, no solo por convención.
4. **Nadie edita el log de auditoría.** Ni el administrador, ni el superusuario técnico.
   No hay ruta por admin de Django, ni por comando de gestión, ni por cascada.
5. **Doble marca de tiempo:** `occurred_at` (reloj del dispositivo) y `recorded_at`
   (reloj del servidor). Los equipos offline mienten con la hora, siempre.
6. **Clave de idempotencia** en toda operación que pueda reenviarse desde la cola offline.
   Reenviar la cola nunca puede duplicar una venta.

## Alternativas descartadas

**Enteros con rangos preasignados por terminal.** Funciona y es más compacta, pero exige
administrar rangos, se rompe al agregar una terminal en caliente y falla silenciosamente
si alguien clona una instalación. Descartada.

**Soft delete con `deleted_at`.** Parece equivalente a append-only y no lo es: sigue
permitiendo `UPDATE` sobre el registro original, con lo que el estado anterior se pierde
y la auditoría queda incompleta. Descartada.

## Consecuencias

- Índices más grandes y joins levemente más costosos que con enteros. Irrelevante al
  volumen de un restaurante.
- Los UUID no son legibles para un humano: por eso la numeración por terminal del punto 2
  existe en paralelo, y es la que ve el cliente en su comprobante.
- La auditoría deja de ser una funcionalidad y pasa a ser una propiedad del modelo de
  datos. Es la diferencia entre un control real y uno decorativo.
