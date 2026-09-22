# Constitución del proyecto `restaurant`

Seis principios innegociables. Cualquier conflicto entre una instrucción y esta
constitución se resuelve a favor de la constitución. Modificarla requiere un ADR.

1. **El negocio nunca deja de cobrar.** La disponibilidad en el punto de venta está por
   encima de la integridad inmediata. Ninguna venta se bloquea por falta de stock, de
   red o de respuesta de un tercero. Lo que se degrada es el registro, y el registro se
   reconcilia después con auditoría completa.

2. **La spec manda.** Si no está en `specs/NNN/spec.md`, no se implementa. Todo requisito
   está numerado en notación EARS y es verificable por un test. Un cambio de alcance se
   hace primero en la spec y recién después en el código.

3. **La historia es inmutable.** Ventas, pagos y movimientos de stock son eventos
   append-only. Una anulación es un evento nuevo, nunca un borrado. Nadie — ni el
   administrador, ni el superusuario — puede editar el registro de auditoría. Un control
   que el dueño puede desactivar no es un control.

4. **Separación de capas y de funciones.** La lógica de negocio vive en servicios, no en
   vistas ni en modelos; los permisos se verifican en el servicio. En el negocio, quien
   cobra no aprueba su propia anulación ni cierra su propio arqueo. Arquitectura limpia
   en el código, segregación de funciones en la operación.

5. **Seguridad y privacidad por diseño y por defecto.** Mínimo privilegio, mínimo dato.
   No se almacena ningún dato de tarjeta más allá de los últimos cuatro dígitos. Toda
   acción sensible deja rastro de auditoría. Lo inseguro no se desactiva: no se escribe.

6. **Verde o no está hecho.** Ninguna tarea se cierra sin `make verify` en verde. Las
   compuertas no se saltan, no se debilitan y no se silencian. Si una compuerta está mal,
   se corrige la compuerta en su propio commit, con justificación.

**Stack por evaluación, no por costumbre.** La elección de stack se documenta en
`specs/NNN/stack.md` con tres candidatos y una recomendación argumentada, aun cuando el
resultado confirme lo que ya se venía usando.

**Idioma.** Código e instrucciones de agentes en inglés. Documentación, specs e interfaz
en español de Paraguay.
