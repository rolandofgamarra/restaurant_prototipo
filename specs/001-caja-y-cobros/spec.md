# Spec 001 — Caja y cobros

**Estado:** aprobada (Rolando, 2026-09-22, incluye revisión del comprobante RF-17..RF-21
— correo en vez de impresión, ver "Dudas abiertas" #8) — lista para `/sdd-stack`

## Contexto y objetivo

Es el núcleo del sistema y el punto donde el negocio gana o pierde dinero: abrir un
turno de caja, cobrar una venta por uno o varios medios de pago, dar vuelto, anular con
autorización, y cerrar el turno con un arqueo que cuadre. Todo esto tiene que funcionar
también cuando no hay internet, porque el requisito que originó el proyecto es que el
local nunca deje de cobrar.

Sin esta spec resuelta, ninguna otra tiene sentido: comandas, inventario y facturación
cuelgan del registro de la venta.

## Usuarios / actores

- **Cajero** — opera la caja y cobra lo que el mozo ya cargó (no toma pedidos; la carga de
  pedidos es de spec 002), cuenta el efectivo al cierre.
- **Supervisor** — autoriza excepciones y cierra el arqueo.
- **Administrador** — no interviene en el turno; consume el resultado para conciliar.

## Historias de usuario

- H1: Como cajero quiero abrir mi turno declarando el fondo inicial para que el arqueo del cierre sea comparable.
- H2: Como cajero quiero cobrar una venta combinando efectivo y medios electrónicos para no rechazar la forma de pago que trae el cliente.
- H3: Como cajero quiero seguir cobrando cuando se cae internet para no cerrar el local.
- H4: Como supervisor quiero que toda anulación posterior al cobro pase por mi PIN para poder responder por las diferencias de mi turno.
- H5: Como supervisor quiero que el cajero cuente el efectivo sin ver el monto esperado para que el arqueo detecte diferencias reales.
- H6: Como administrador quiero que el disponible en caja cuente solo el efectivo para que la conciliación bancaria sea posible.

## Requisitos funcionales

### Sesión de caja

- RF-1: CUANDO un cajero abre una sesión de caja, EL SISTEMA registrará el fondo inicial declarado, la terminal, el actor y la marca de tiempo.
- RF-2: SI un cajero intenta abrir una sesión en una terminal que ya tiene una sesión abierta, ENTONCES EL SISTEMA rechazará la apertura e informará qué sesión está abierta y desde cuándo.
- RF-3: MIENTRAS una sesión de caja está abierta, EL SISTEMA permitirá registrar ventas, cobros, sangrías y anulaciones contra esa sesión.
- RF-4: CUANDO un cajero distinto de quien abrió la sesión activa de la terminal registra una operación, EL SISTEMA registrará a ese cajero como actor de la operación, sin cerrar ni reabrir la sesión (la sesión es de la terminal; el cajero activo se registra por operación).
- RF-5: SI se intenta registrar un cobro sin sesión de caja abierta, ENTONCES EL SISTEMA rechazará la operación e informará que debe abrirse la caja.
- RF-6: CUANDO un cajero registra una sangría, EL SISTEMA descontará el monto del disponible en efectivo y registrará el motivo y el actor.

### Cobro

- RF-7: EL SISTEMA expresará todos los montos en guaraníes enteros, sin decimales.
- RF-8: CUANDO se registra un cobro, EL SISTEMA aceptará uno o más pagos por venta, con los medios: efectivo, QR, tarjeta de débito, tarjeta de crédito y transferencia.
- RF-9: CUANDO la suma de los pagos de una venta es menor al total, EL SISTEMA mantendrá la venta abierta e informará el saldo pendiente.
- RF-10: SI la suma de los pagos no-efectivo supera el total de la venta, ENTONCES EL SISTEMA rechazará el cobro e informará el exceso.
- RF-11: CUANDO el pago en efectivo supera el saldo pendiente, EL SISTEMA calculará el vuelto redondeado al múltiplo configurado en `REDONDEO_VUELTO_GS`.
- RF-12: CUANDO se registra un pago electrónico, EL SISTEMA exigirá una referencia (número de lote, transacción o últimos cuatro dígitos) y lo marcará como pendiente de conciliación.
- RF-13: EL SISTEMA contabilizará como disponible en efectivo únicamente los pagos en efectivo.
- RF-14: CUANDO se registra una propina, EL SISTEMA la registrará como una línea separada que no integra el total de la venta, atribuida al mozo que atendió (la entidad mozo se define en spec 002; esta spec solo almacena la referencia).
- RF-15: EL SISTEMA garantizará que la suma de los totales de línea sea igual al total de la venta tras el redondeo.
- RF-16: SI la misma operación de cobro se recibe más de una vez con la misma clave de idempotencia, ENTONCES EL SISTEMA registrará una sola venta y devolverá el resultado de la primera.
- RF-17: CUANDO un cobro completa el total de la venta y el cliente no solicita factura formal, EL SISTEMA ofrecerá al cajero capturar el correo electrónico del cliente para enviarle el comprobante.
- RF-18: SI el cajero captura un correo electrónico al completar el cobro, ENTONCES EL SISTEMA enviará el comprobante de la venta a esa dirección.
- RF-19: SI el cliente no provee un correo electrónico, ENTONCES EL SISTEMA completará el cobro sin enviar comprobante, dejando la venta registrada para auditoría interna.
- RF-20: SI no hay conexión a internet en el momento de enviar el comprobante, ENTONCES EL SISTEMA encolará el envío y lo completará automáticamente al restablecerse la conexión, sin bloquear el cobro.
- RF-21: SI un cliente solicita una factura con validez fiscal, ENTONCES EL SISTEMA informará que la facturación electrónica no está disponible en esta versión y ofrecerá el comprobante interno como alternativa.

### Descuentos y anulaciones

- RF-22: CUANDO un cajero aplica un descuento menor o igual al tope configurado, EL SISTEMA lo aceptará sin autorización adicional.
- RF-23: SI un cajero aplica un descuento superior al tope configurado, ENTONCES EL SISTEMA exigirá el PIN de un supervisor antes de aceptarlo.
- RF-24: EL SISTEMA no exigirá un tope adicional a los descuentos ya autorizados con PIN de supervisor.
- RF-25: CUANDO un cajero anula un ítem de una venta aún no cobrada, EL SISTEMA lo aceptará sin autorización y registrará el evento.
- RF-26: SI se intenta anular una venta ya cobrada, ENTONCES EL SISTEMA exigirá el PIN de un supervisor y un motivo de la siguiente lista cerrada: error de cobro, reclamo del cliente, pedido cancelado por el cliente.
- RF-27: CUANDO se anula una venta cobrada, EL SISTEMA creará un evento de anulación que referencia a la venta original, sin modificarla ni eliminarla.
- RF-28: CUANDO se ejecuta una acción que requirió autorización, EL SISTEMA registrará un evento de auditoría con actor, autorizador, motivo y marca de tiempo.
- RF-29: SI el actor y el autorizador de un evento de auditoría son la misma persona, ENTONCES EL SISTEMA marcará el evento como autoautorizado (ver ADR 0004).

### Arqueo y cierre

- RF-30: CUANDO un cajero inicia el cierre de su sesión, EL SISTEMA solicitará el conteo de efectivo sin mostrar el monto esperado.
- RF-31: CUANDO se registra el conteo, EL SISTEMA calculará la diferencia entre el efectivo contado y el esperado, y exigirá el PIN de un supervisor para cerrar la sesión.
- RF-32: CUANDO se cierra una sesión, EL SISTEMA emitirá un resumen con: fondo inicial, ventas por medio de pago, sangrías, efectivo esperado, efectivo contado y diferencia.
- RF-33: SI una sesión de caja lleva más de 8 horas abierta, ENTONCES EL SISTEMA alertará al supervisor.

### Operación degradada

- RF-34: EL SISTEMA mostrará de forma permanente en la pantalla de caja el nivel de operación vigente (N0 a N4).
- RF-35: MIENTRAS el sistema opera sin conexión a internet, EL SISTEMA permitirá cobrar en efectivo con funcionalidad completa.
- RF-36: MIENTRAS el sistema opera sin conexión a internet, EL SISTEMA aceptará pagos electrónicos declarados por el cajero con su referencia, marcándolos como pendientes de conciliación.
- RF-37: CUANDO se restablece la conexión, EL SISTEMA sincronizará las operaciones encoladas en orden y sin duplicar.
- RF-38: EL SISTEMA registrará en cada venta la marca de tiempo del dispositivo y la del servidor.
- RF-39: SI el stock de un producto es insuficiente, ENTONCES EL SISTEMA registrará la venta igualmente y emitirá una alerta de stock negativo.

## Requisitos no funcionales

- El registro de un cobro debe completarse en menos de 500 ms en la terminal, medido en el equipo de caja de referencia, operando contra el servidor local.
- Ningún dato de tarjeta más allá de los últimos cuatro dígitos se almacena en ninguna circunstancia.
- La interfaz de caja es operable íntegramente por teclado, sin depender del mouse.
- Toda la interfaz y todos los mensajes de error en español de Paraguay.

## Casos límite

- Pago exacto; pago de más con vuelto; pago de menos.
- Pago mixto cuyas partes suman exactamente el total, y cuyas partes no suman.
- Vuelto que no es múltiplo del redondeo configurado.
- Descuento exactamente en el tope, uno menos y uno más.
- Anulación de una venta que ya fue anulada.
- La misma operación llegando dos veces desde la cola offline.
- Reloj del dispositivo adelantado y atrasado respecto del servidor.
- Dos terminales cobrando contra la misma mesa a la vez.
- Arqueo con sobrante, con faltante y exacto.
- Cajero que abandona el turno sin cerrar la caja.
- Corte de energía o de internet entre el cobro y el envío del comprobante por correo.
- Cliente que pide factura formal y el cajero debe explicarle que aún no está disponible.
- Cliente que da un correo electrónico con formato inválido.

## Fuera de alcance

- Facturación electrónica y SIFEN (documento con validez fiscal, RUC del cliente,
  contingencia impresa). Se cubre en una spec dedicada, número a definir cuando se
  redacte, que se lee sobre la documentación oficial en `docs/dumentacion_SIFEN/`. Spec
  001 solo cubre el comprobante interno sin valor fiscal (RF-17 a RF-21); cuando el
  cliente pide factura formal, RF-21 define qué le informa el cajero mientras tanto.
- Integración directa con la API de Bancard. En esta spec el pago con tarjeta se registra
  como declarado por el cajero con su referencia.
- Comandas a cocina, mesas y mozos (spec 002).
- Inventario y recetas (spec 003).
- Compras, proveedores y conciliación bancaria (spec 004).
- Analítica de negocio (spec 005).
- Modo N3 y N4 completos: en esta spec se cubren N0, N1 y N2.

## Criterios de finalización

- Todos los RF con al menos un test en verde y mapeados en `validation.md`.
- `make ship` en verde.
- Demo manual: abrir caja, cobrar tres ventas (efectivo, mixto, electrónico), aplicar un
  descuento sobre el tope con autorización, anular una venta cobrada, cerrar con arqueo
  ciego y diferencia justificada.
- Demo manual del modo degradado: desconectar la red durante la operación, cobrar, y
  verificar que al reconectar no se duplica ninguna venta.

## Dudas abiertas

Ninguna. Las 8 marcadas `[NECESITA ACLARACIÓN]` de la auditoría de fase 0.5 fueron
resueltas por Rolando el 2026-09-22:

1. El cajero solo cobra; no toma pedidos (carga del mozo, spec 002). Ver "Usuarios / actores".
2. La sesión es por terminal; el cajero activo se registra por operación (RF-4).
3. La propina se atribuye al mozo que atendió (RF-14); la entidad mozo se define en spec 002.
4. El supervisor no tiene tope de descuento superior (RF-20).
5. Lista cerrada de motivos de anulación: error de cobro, reclamo del cliente, pedido
   cancelado por el cliente (RF-22).
6. Alerta de sesión abierta: 8 horas (RF-33).
7. Comprobante: no se imprime. Si el cliente no pide factura formal, se envía por correo
   si el cajero captura el email; si no lo da, la venta queda igual registrada para
   auditoría interna, sin comprobante enviado (RF-17 a RF-19). Decisión revisada el
   2026-09-22: ver punto 8.

8. [Revisión 2026-09-22] Se reemplazó la impresión de ticket por envío de comprobante
   por correo. Al indagar el motivo surgió que lo que el negocio necesita en algunos
   casos es una **factura con validez fiscal (SIFEN)**, no un simple ticket — eso excede
   el alcance de esta spec y de esta fase. Decisión: spec 001 solo implementa el
   comprobante interno (RF-17 a RF-21); la facturación electrónica SIFEN queda para una
   spec dedicada y depende de esta (ver "Fuera de alcance"). RF-21 cubre qué le dice el
   sistema al cajero cuando el cliente pide factura formal mientras esa spec no existe.
9. Cola de envío sin internet: se encola y se envía automático al reconectar, igual que
   la cola de sincronización general (RF-20, RF-37).
10. Cliente que no da email y no pide factura: se omite el envío, la venta queda
    registrada igual para auditoría interna (RF-19).
