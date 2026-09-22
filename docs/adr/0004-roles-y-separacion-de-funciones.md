# ADR 0004 — Roles y separación de funciones

**Estado:** aceptada
**Fecha:** 2026-09-22 (aprobada por Rolando el 2026-09-22)

## Contexto

El requisito inicial asignaba al cajero cobro, anulación, descuentos, facturación y
arqueo de caja, sin restricción. Esas cinco facultades en una sola persona concentran la
mayor parte de las pérdidas conocidas en gastronomía: se cobra al cliente, se anula el
ticket después, y la diferencia se va con el efectivo. Lo mismo ocurre con descuentos
discrecionales y con el arqueo cerrado por quien manejó la caja.

Se planteó además si conviene tener supervisor y administrador como roles separados.

## Decisión

**Cuatro roles humanos, más un rol técnico y perfiles de estación.** Un usuario puede
tener más de un rol: en un local chico la misma persona será supervisor y administrador,
pero los roles no se fusionan — cuando el negocio crezca no hay refactor.

**Cajero.** Cobro en todos los medios y en pagos mixtos, vuelto, propina, apertura y
cierre de su turno con fondo declarado, anulación libre de ítems *antes* del cobro,
descuento hasta un tope configurado, emisión de comprobante, sangría a caja fuerte,
arqueo ciego. No ve costos, márgenes, otras cajas ni histórico.

**Supervisor** (autoridad operativa del turno, presente en el salón). Todo lo anterior,
más: autorizar anulaciones post-cobro, devoluciones, descuentos sobre el tope y
cortesías; abrir y forzar el cierre de cajas ajenas; aprobar el arqueo y justificar la
diferencia; transferir mesas, unir y dividir cuentas, reasignar mozo; gestionar comandas;
marcar producto agotado; registrar mermas y consumo del personal dentro de un tope; ver
el tablero del turno. No toca precios de lista, costos, proveedores, conciliación ni
usuarios.

**Administrador** (autoridad económica y de configuración, puede no estar en el local).
Todo lo anterior, más: conciliación bancaria y disponible en efectivo y en banco;
compras, proveedores y cuentas por pagar; inventario, recetas, costos y puntos de
reposición; carta, precios y topes de descuento por rol; usuarios, PIN y comisiones;
analítica de negocio; y el log completo de auditoría con ranking de anulaciones,
descuentos y diferencias de arqueo por usuario.

**Mozo.** Toma el pedido en mesa desde el celular y envía la comanda. No cobra.

**Superusuario técnico.** Errores, migraciones y soporte. Sus acciones también se
registran y son visibles para el administrador.

**Cocina** es un perfil de estación (dispositivo), no un rol de persona.

**Mecanismo de autorización.** El cajero *inicia*, el supervisor *autoriza con su PIN en
la misma pantalla* — sin cerrar sesión. Cada autorización genera un evento de auditoría
con actor, autorizador, motivo de una lista cerrada y marca de tiempo.

**Auto-autorización (local de una sola persona).** El sistema no impide que actor y
autorizador sean la misma persona — sería inoperable en un local de un único empleado.
En su lugar, todo evento de auditoría donde actor y autorizador coincidan se marca como
autoautorizado, visible en el ranking de anulaciones/descuentos del administrador
(ver rol Administrador). Es un control de detección, no de prevención — decisión de
Rolando, 2026-09-22.

**Arqueo ciego.** El cajero cuenta sin ver el monto esperado por el sistema; el
supervisor cierra y justifica la diferencia.

## Alternativa descartada

**Un único rol "encargado"** que cubra supervisor y administrador. Más simple de
implementar y elimina la separación de funciones, que es justamente el control que
justifica el módulo de auditoría. Descartada: se logra el mismo ahorro operativo
asignando ambos roles a un mismo usuario, sin perder la separación en el modelo.

## Consecuencias

- Los permisos se verifican en la capa de servicios, nunca solo en la vista o el template.
- Todo tope (porcentaje y monto de descuento, monto de ajuste de stock) es configuración,
  no constante.
- La operación gana un paso: el supervisor tiene que estar disponible en el turno. Es el
  costo del control, y es deliberado.
