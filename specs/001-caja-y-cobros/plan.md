# Plan técnico — Spec 001: Caja y cobros

**Estado:** aprobado (Rolando, 2026-09-22). Supuestos S1, S2 y S3 confirmados tal como
quedaron redactados. Habilita `/sdd-tasks`.
**Fecha:** 2026-09-22
**Entradas:** `docs/constitution.md`, `docs/ARCHITECTURE.md`,
`specs/001-caja-y-cobros/spec.md` (aprobada, RF-1..RF-39),
`specs/001-caja-y-cobros/stack.md` (aprobado), ADR 0001/0002/0003/0004.

Este documento es el contrato de construcción. El bucle de construcción lee **solo** los
archivos que este plan nombra. Si un archivo no está declarado acá, el implementador no
lo abre: pide una corrección del plan.

No contiene código de producción. Los bloques de pseudocódigo son especificación de
comportamiento, no implementación.

---

## 0. Supuestos marcados

Los tres supuestos que tuve que resolver para que el plan sea ejecutable. Cada uno
necesita confirmación de Rolando en la aprobación.

- **S1 — Referencia al producto sin `catalog`.** La spec 001 no define la carta (es spec
  002/003) pero `LineaVenta` necesita identificar qué se vendió. Resuelvo con
  **snapshot denormalizado**: `producto_id` (UUID, nullable, sin FK), `descripcion` y
  `precio_unitario_gs` congelados al momento de la venta. No hay FK a `catalog`. Esto es
  correcto con independencia de spec 001: el precio de una venta histórica nunca debe
  cambiar porque cambió la carta. Cuando exista `catalog`, el `producto_id` pasa a
  resolver contra él sin migración de datos.
- **S2 — Alcance real de RF-39 sin `inventory`.** No hay insumos ni stock en spec 001
  (eso es spec 003), así que "stock insuficiente" no es observable todavía. Implemento la
  mitad que sí es verificable hoy y que es la que importa: un **puerto no bloqueante**
  `inventory/services/stock.py`, invocado por el cobro **después** del commit y envuelto
  de forma que ninguna excepción suya pueda revertir la venta, más un evento de auditoría
  `ALERTA_STOCK_NEGATIVO`. El test de RF-39 inyecta un puerto que explota y verifica que
  la venta queda cobrada igual. La lógica de cálculo de stock llega en spec 003 y se
  enchufa en ese mismo puerto.
- **S3 — App `notifications/` es nueva y `ARCHITECTURE.md` §3 hay que actualizarlo.** Ver
  decisión D1. La actualización de `ARCHITECTURE.md` es una tarea de documentación dentro
  de esta spec, no un ADR nuevo (no cambia ninguna decisión aceptada, agrega un contexto
  acotado que el `stack.md` aprobado ya nombra por ruta).

Ninguna otra ambigüedad quedó sin resolver: los 39 RF tienen cobertura (sección 7).

---

## 1. Estructura de módulos

### 1.1 Grafo de dependencias

Se verifica en G1. La flecha se lee "puede importar a".

```
shared  <-  domain  <-  { accounts, cash, orders, payments, audit, sync,
                          notifications, inventory }  <-  views/templates

Entre apps (solo por servicio, nunca importando modelos ajenos):

  payments  ->  orders  ->  cash  ->  accounts
      |            |          |          ^
      |            +----------+----------+
      v
  notifications        (todas)  ->  audit
  inventory                     ->  sync
```

`cash` no conoce `payments`. `orders` no conoce `payments`. `notifications` no conoce
`cash` ni `payments`: recibe un DTO de comprobante y una dirección. Esto es lo que
permite que el transporte del correo sea intercambiable sin tocar caja (restricción del
`stack.md`).

### 1.2 `src/shared/` — primitivas sin dependencias

| Archivo | Responsabilidad | RF |
|---|---|---|
| `shared/money.py` | `redondear_gs(monto:int, multiplo:int) -> int` (único punto de redondeo del sistema, ADR 0002), `cuadrar_lineas(total_gs, lineas) -> list[int]`, `formatear_gs`. | RF-7, RF-11, RF-15 |
| `shared/clock.py` | `Clock` (Protocol con `now() -> datetime`), `RelojSistema`, `RelojFijo`. El tiempo entra por parámetro, nunca se lee `timezone.now()` dentro de la lógica. | RF-1, RF-33, RF-38 |
| `shared/ids.py` | `GeneradorUuid` (Protocol), `UuidAleatorio`, `UuidSecuencial` (tests), `nueva_clave_idempotencia()`. | RF-16 |
| `shared/result.py` | `Resultado[T]` / `Error` — mecanismo preferido para que los servicios devuelvan flujo de negocio esperado sin lanzar excepciones. No es el único mecanismo: ver nota 2026-09-22. | transversal |
| `shared/errors.py` | Jerarquía base `ErrorDeNegocio` (hereda de `Exception`, ver nota 2026-09-22) con `codigo` y `mensaje` en español. | transversal |
| `shared/mensajes.py` | Cadenas de cara al usuario, español de Paraguay, un solo lugar. | RF-2, RF-5, RF-9, RF-10, RF-21 |

> **Nota (2026-09-22):** code review de T5 encontró que esta fila contradecía el
> pseudocódigo de §3.3/§3.4, que usa `lanzar ExcesoNoEfectivo(...)`, `lanzar SinSesion`,
> `lanzar PinBloqueado`, etc. Se corrige: `Resultado[T]` sigue siendo el mecanismo
> preferido para el flujo de negocio esperado en general, pero no es exclusivo.
> `ErrorDeNegocio` hereda de `Exception` y se puede lanzar con `raise`/capturar con
> `except` donde el pseudocódigo de otras secciones del plan ya lo especifica así. Cada
> servicio/RF elige el mecanismo (`Resultado[T]` o `raise ErrorDeNegocio`) que le quede
> mejor; no son mutuamente excluyentes.

### 1.3 `src/domain/` — reglas puras, importable sin Django

Ningún import de `django.*` acá. Todo recibe datos planos (dataclasses) y devuelve datos
planos. Es el material del G2 con cobertura ≥ 85%.

| Archivo | Responsabilidad | RF |
|---|---|---|
| `domain/enums.py` | `MedioPago`, `EstadoVenta`, `EstadoPago`, `MotivoAnulacion` (lista cerrada de RF-26), `TipoEvento`, `NivelOperacion` (N0..N4), `EstadoEnvio`. | RF-8, RF-26, RF-34 |
| `domain/cobro.py` | `asignar_pagos(...)` — validación y asignación de pago mixto, saldo pendiente, exceso no-efectivo. | RF-8, RF-9, RF-10 |
| `domain/vuelto.py` | `calcular_vuelto(...)` — vuelto bruto, vuelto redondeado y **ajuste de redondeo** explícito. | RF-11 |
| `domain/venta.py` | `recalcular_totales(lineas)` con la regla de cuadre de ADR 0002 (redondea el total, ajusta la última línea vigente). | RF-15, RF-25 |
| `domain/descuentos.py` | `evaluar_descuento(monto, tope_pct, tope_gs, autorizado: bool)` → `LIBRE` / `REQUIERE_PIN` / `ACEPTADO_POR_AUTORIZACION`. | RF-22, RF-23, RF-24 |
| `domain/arqueo.py` | `calcular_esperado(fondo, pagos_efectivo, vueltos, ajustes_redondeo, sangrias)`, `calcular_diferencia(esperado, contado)`. | RF-30, RF-31, RF-32 |
| `domain/disponible.py` | `disponible_en_efectivo(...)` — solo efectivo suma. | RF-13 |
| `domain/sesion.py` | `sesion_prolongada(abierta_en, ahora, horas_limite) -> bool`. | RF-33 |
| `domain/errores.py` | `SaldoInsuficiente`, `ExcesoNoEfectivo`, `ReferenciaRequerida`, `MotivoInvalido`, `AutorizacionRequerida`. | RF-10, RF-12, RF-23, RF-26 |

### 1.4 `src/accounts/` — usuarios, roles, PIN

| Archivo | Responsabilidad | RF |
|---|---|---|
| `accounts/models.py` | `Usuario` (PK UUID, hereda `AbstractUser`), `pin_hash`, bloqueo por intentos. Roles vía `Group` con slugs fijos (ADR 0004). | RF-4 |
| `accounts/services/autorizacion.py` | `verificar_pin_supervisor(pin, actor, motivo, clock) -> Autorizacion`. **Único** lugar donde se valida un PIN. Devuelve el value object que los demás servicios exigen como parámetro. Marca `autoautorizado` si `actor == autorizador`. | RF-23, RF-26, RF-28, RF-29, RF-31 |
| `accounts/services/permisos.py` | `exigir_rol(usuario, rol)` — chequeo de rol **en capa de servicio** (constitución §4). | RF-3, RF-6, RF-25 |
| `accounts/selectors.py` | Lectura de usuario por PIN-id sin exponer el hash. | — |
| `accounts/admin.py` | Alta de usuarios y carga de PIN (nunca muestra el PIN). | — |

### 1.5 `src/cash/` — sesión de caja, sangría, arqueo

| Archivo | Responsabilidad | RF |
|---|---|---|
| `cash/models.py` | `Terminal`, `SesionCaja`, `Sangria`. | RF-1, RF-2, RF-6 |
| `cash/services/sesion.py` | `abrir_sesion(...)`, `sesion_activa(terminal)`, `exigir_sesion_abierta(terminal)`. | RF-1, RF-2, RF-3, RF-4, RF-5 |
| `cash/services/sangria.py` | `registrar_sangria(...)` — `atomic()` + `select_for_update()` sobre la sesión. | RF-6 |
| `cash/services/arqueo.py` | `iniciar_cierre(...)` (no devuelve el esperado), `registrar_conteo(...)` (conteo primero, esperado después, PIN obligatorio). | RF-30, RF-31 |
| `cash/services/resumen.py` | `resumen_de_cierre(sesion) -> ResumenCierre`. Consume `payments` por servicio, no importa `Pago`. | RF-32 |
| `cash/tasks.py` | `alertar_sesiones_prolongadas()` — Celery beat cada 15 min, reloj inyectado. | RF-33 |
| `cash/views/sesion.py` | Apertura, sangría, panel de caja. Parsea y renderiza, nada más. | RF-1, RF-6 |
| `cash/views/cierre.py` | Pantalla de conteo ciego y resumen. | RF-30, RF-32 |
| `cash/forms.py` | `AperturaForm`, `SangriaForm`, `ConteoForm`. Validación de formato, no de negocio. | — |
| `cash/templates/cash/*.html` | `apertura.html`, `panel.html`, `sangria.html`, `conteo_ciego.html`, `resumen_cierre.html`, `_nivel_operacion.html`. | RF-30, RF-32, RF-34 |

### 1.6 `src/orders/` — venta, líneas, descuentos, anulación de ítem

La `Venta` vive acá y no en `payments`: es el documento de venta que spec 002 extiende
con mesa, mozo y comanda. Así `payments` depende de `orders` y nunca al revés.

| Archivo | Responsabilidad | RF |
|---|---|---|
| `orders/models.py` | `Venta`, `LineaVenta`, `SecuenciaTerminal`. | RF-15, RF-27, RF-38 |
| `orders/services/venta.py` | `crear_venta(...)`, `agregar_linea(...)`, `recalcular(...)`. | RF-15, RF-38 |
| `orders/services/numeracion.py` | `siguiente_numero(terminal)` — establecimiento + punto de expedición + secuencia local, con `select_for_update()` (ADR 0003 §2). | RF-38 |
| `orders/services/descuento.py` | `aplicar_descuento(..., autorizacion: Autorizacion \| None)`. | RF-22, RF-23, RF-24 |
| `orders/services/anulacion_item.py` | `anular_linea(...)` — solo si la venta está ABIERTA, sin autorización, con evento. | RF-25 |
| `orders/views/venta.py` | Pantalla de la venta abierta. | RF-9, RF-25 |
| `orders/templates/orders/*.html` | `venta_abierta.html`, `_lineas.html`, `_descuento_pin.html`. | RF-22, RF-23 |

### 1.7 `src/payments/` — cobro, medios de pago, vuelto, propina, anulación post-cobro

| Archivo | Responsabilidad | RF |
|---|---|---|
| `payments/models.py` | `Pago`, `Propina`. | RF-8, RF-12, RF-13, RF-14 |
| `payments/services/cobro.py` | `registrar_cobro(...)` — orquestador. `atomic()` + `select_for_update()` sobre `SesionCaja`, idempotencia, asignación de pagos, vuelto, transición de estado, disparo de auditoría, comprobante y stock. | RF-8..RF-13, RF-16, RF-17..RF-19, RF-35, RF-36, RF-39 |
| `payments/services/propina.py` | `registrar_propina(...)` — línea aparte, fuera del total, atribuida al mozo. | RF-14 |
| `payments/services/anulacion_venta.py` | `anular_venta_cobrada(...)` — exige `Autorizacion` + motivo de la lista cerrada, crea `Venta` tipo ANULACION que referencia la original. | RF-26, RF-27 |
| `payments/selectors.py` | `pagos_por_medio(sesion)`, `efectivo_disponible(sesion)` — API que `cash` consume sin importar modelos. | RF-13, RF-32 |
| `payments/messages.py` | Mensaje de RF-21 (factura formal no disponible) y mensajes de error de cobro. | RF-21 |
| `payments/views/cobro.py` | Pantalla de cobro, operable por teclado. | RF-8..RF-12, RF-17 |
| `payments/views/anulacion.py` | Anulación con PIN y motivo. | RF-26 |
| `payments/forms.py` | `PagoForm`, `CobroForm`, `EmailComprobanteForm`, `AnulacionForm`. | RF-12, RF-17, RF-26 |
| `payments/templates/payments/*.html` | `cobro.html`, `_pago_linea.html`, `_vuelto.html`, `_email_comprobante.html`, `_pin_supervisor.html`, `anulacion.html`, `_factura_no_disponible.html`. | RF-11, RF-17, RF-21, RF-26 |

**No se crea** `payments/gateways/`. Spec 001 no integra Bancard (fuera de alcance): el
pago electrónico es declarado por el cajero con su referencia. Crear el puerto ahora sería
una interfaz sin implementación, prohibida por los anti-objetivos.

### 1.8 `src/audit/` — log append-only

| Archivo | Responsabilidad | RF |
|---|---|---|
| `audit/models.py` | `EventoAuditoria`. `delete()` y el `UPDATE` sobre un registro existente lanzan; manager sin `delete()`. | RF-27, RF-28, RF-29 |
| `audit/services/registro.py` | `registrar_evento(tipo, actor, autorizacion, objeto, payload, clock)`. Única puerta de escritura. | RF-28, RF-29 |
| `audit/selectors.py` | Consultas por tipo, actor y `autoautorizado`. | RF-29 |
| `audit/migrations/0002_revocar_permisos.py` | `REVOKE UPDATE, DELETE` sobre la tabla del log para el rol de aplicación (control real, no convención). | RF-28 |

### 1.9 `src/sync/` — idempotencia, cola offline, nivel de degradación

| Archivo | Responsabilidad | RF |
|---|---|---|
| `sync/models.py` | `RegistroIdempotencia`, `OperacionEncolada`. | RF-16, RF-37 |
| `sync/services/idempotencia.py` | `ejecutar_idempotente(clave, tipo, fn)` — decorador de servicio que garantiza una sola escritura y devuelve el resultado de la primera. | RF-16 |
| `sync/services/cola.py` | `encolar(...)`, `drenar(limite, clock)` — orden estable, sin duplicar. | RF-37 |
| `sync/services/nivel.py` | `nivel_actual(sondas, clock) -> NivelOperacion`. Sondas inyectadas (internet, LAN, edge box). | RF-34, RF-35, RF-36 |
| `sync/context_processors.py` | `nivel_operacion` — disponible en todo template de caja. | RF-34 |
| `sync/tasks.py` | `drenar_cola()` — Celery, reintento con backoff. | RF-37 |

### 1.10 `src/notifications/` — comprobante por correo (app NUEVA)

| Archivo | Responsabilidad | RF |
|---|---|---|
| `notifications/models.py` | `EnvioComprobante`. | RF-18, RF-20 |
| `notifications/providers/base.py` | Puerto propio: `ProveedorCorreo` (Protocol), `MensajeCorreo`, `ResultadoEnvio(ok, mensaje_id, error, reintentable)`. Ningún tipo de AWS cruza este límite. | RF-18 |
| `notifications/providers/ses.py` | Adaptador Amazon SES (proveedor concreto del `stack.md`). | RF-18 |
| `notifications/providers/consola.py` | Adaptador de desarrollo: escribe a log. | — |
| `notifications/providers/memoria.py` | Adaptador de test: acumula en lista, permite forzar fallos. | RF-18, RF-20 |
| `notifications/services/comprobante.py` | `encolar_comprobante(venta_dto, email, clock)`, `despachar(envio, proveedor, clock)`. Renderiza el comprobante y decide reintento vs. descarte. | RF-18, RF-19, RF-20 |
| `notifications/tasks.py` | `enviar_comprobante(envio_id)` y `reintentar_pendientes()` — Celery. **Nunca** síncrono en la vista. | RF-18, RF-20 |
| `notifications/templates/notifications/comprobante.html` / `.txt` | Cuerpo del correo. Sin valor fiscal, con leyenda explícita. | RF-18, RF-21 |

### 1.11 `src/inventory/` — solo el puerto no bloqueante (S2)

| Archivo | Responsabilidad | RF |
|---|---|---|
| `inventory/services/stock.py` | `descontar_por_venta(venta_dto) -> AvisoStock \| None`. En spec 001 es un no-op que puede ser reemplazado. Se invoca fuera del `atomic()` del cobro y toda excepción suya se captura y se convierte en evento de auditoría. | RF-39 |

### 1.12 `src/config/`

| Archivo | Responsabilidad | RF |
|---|---|---|
| `config/settings/base.py` | `REDONDEO_VUELTO_GS`, `TOPE_DESCUENTO_PORCENTAJE`, `TOPE_DESCUENTO_GS`, `HORAS_ALERTA_SESION=8`, `REMITENTE_COMPROBANTE`, `PROVEEDOR_CORREO`. Todo tope es configuración, nunca constante (ADR 0004). | RF-11, RF-22, RF-33 |
| `config/settings/test.py` | Reloj fijo, proveedor de correo en memoria, Celery `task_always_eager=False` + ejecución manual. | — |
| `config/celery.py` | App Celery y beat schedule (`alertar_sesiones_prolongadas`, `drenar_cola`, `reintentar_pendientes`). | RF-20, RF-33, RF-37 |
| `config/urls.py` | Rutas de caja, cobro, cierre. | — |

---

## 2. Modelo de datos

Reglas que aplican a **todos** los modelos de abajo: PK `UUIDField(primary_key=True,
default=uuid4, editable=False)`; todo monto `BigIntegerField` en guaraníes enteros;
`occurred_at` (reloj del dispositivo) y `recorded_at` (reloj del servidor) en toda entidad
creable offline; `on_delete=PROTECT` en todas las FK; `delete()` sobrescrito para lanzar
en `Venta`, `LineaVenta`, `Pago`, `Propina`, `EventoAuditoria`, `Sangria`.

### 2.1 `accounts.Usuario`

| Campo | Tipo Django | Notas |
|---|---|---|
| `id` | `UUIDField(pk)` | |
| (campos de `AbstractUser`) | | `username`, `first_name`, `is_active`… |
| `pin_hash` | `CharField(max_length=128, blank=True)` | PBKDF2 vía `make_password`. Nunca el PIN en claro. |
| `pin_actualizado_en` | `DateTimeField(null=True)` | |
| `pin_intentos_fallidos` | `PositiveSmallIntegerField(default=0)` | |
| `pin_bloqueado_hasta` | `DateTimeField(null=True, blank=True)` | Bloqueo temporal tras 5 fallos. |

Roles vía `Group` con slugs fijos: `CAJERO`, `SUPERVISOR`, `ADMINISTRADOR`, `MOZO`,
`SOPORTE`. Un usuario puede tener varios (ADR 0004).

Fila de ejemplo: `id=3f2a…`, `username="mcabral"`, `first_name="Mirta"`,
`pin_hash="pbkdf2_sha256$870000$…"`, grupos `{CAJERO}`.

### 2.2 `cash.Terminal`

| Campo | Tipo | Notas |
|---|---|---|
| `id` | `UUIDField(pk)` | |
| `codigo` | `CharField(max_length=16, unique=True)` | `CAJA-01` |
| `nombre` | `CharField(max_length=60)` | |
| `establecimiento` | `CharField(max_length=3)` | `001` — ADR 0003 §2 |
| `punto_expedicion` | `CharField(max_length=3)` | `001` |
| `activa` | `BooleanField(default=True)` | |

Ejemplo: `codigo="CAJA-01"`, `nombre="Caja mostrador"`, `establecimiento="001"`,
`punto_expedicion="001"`.

### 2.3 `cash.SesionCaja` — RF-1..RF-6, RF-30..RF-33

| Campo | Tipo | Notas |
|---|---|---|
| `id` | `UUIDField(pk)` | |
| `terminal` | `ForeignKey(Terminal, PROTECT, related_name="sesiones")` | La sesión es **de la terminal** (RF-4) |
| `cajero_apertura` | `ForeignKey(Usuario, PROTECT, related_name="sesiones_abiertas")` | Quién abrió, no quién opera |
| `fondo_inicial_gs` | `BigIntegerField` | |
| `estado` | `CharField(max_length=10, choices=EstadoSesion)` | `ABIERTA` / `CERRADA` |
| `abierta_occurred_at` | `DateTimeField` | reloj del dispositivo |
| `abierta_recorded_at` | `DateTimeField` | reloj del servidor |
| `cerrada_occurred_at` | `DateTimeField(null=True, blank=True)` | |
| `cerrada_recorded_at` | `DateTimeField(null=True, blank=True)` | |
| `efectivo_contado_gs` | `BigIntegerField(null=True, blank=True)` | se persiste **antes** de calcular el esperado (RF-30) |
| `efectivo_esperado_gs` | `BigIntegerField(null=True, blank=True)` | |
| `diferencia_gs` | `BigIntegerField(null=True, blank=True)` | contado − esperado |
| `supervisor_cierre` | `ForeignKey(Usuario, PROTECT, null=True, related_name="cierres")` | RF-31 |
| `alerta_prolongada_emitida` | `BooleanField(default=False)` | evita alertas repetidas (RF-33) |
| `clave_idempotencia` | `CharField(max_length=64, unique=True)` | |

Constraints e índices:

```python
UniqueConstraint(fields=["terminal"], condition=Q(estado="ABIERTA"),
                 name="unica_sesion_abierta_por_terminal")          # RF-2
CheckConstraint(check=Q(fondo_inicial_gs__gte=0), name="fondo_no_negativo")
CheckConstraint(check=Q(estado="ABIERTA", cerrada_recorded_at__isnull=True)
                      | Q(estado="CERRADA", cerrada_recorded_at__isnull=False),
                name="cierre_consistente")
Index(fields=["estado", "abierta_recorded_at"])                      # RF-33
```

Fila de ejemplo: `terminal=CAJA-01`, `cajero_apertura=mcabral`, `fondo_inicial_gs=300000`,
`estado="ABIERTA"`, `abierta_occurred_at=2026-09-22T11:02:14-03`,
`abierta_recorded_at=2026-09-22T11:02:16-03`, `efectivo_contado_gs=None`,
`clave_idempotencia="ses-CAJA01-20260922-110214-a91c"`.

### 2.4 `cash.Sangria` — RF-6

| Campo | Tipo |
|---|---|
| `id` | `UUIDField(pk)` |
| `sesion` | `ForeignKey(SesionCaja, PROTECT, related_name="sangrias")` |
| `actor` | `ForeignKey(Usuario, PROTECT)` |
| `monto_gs` | `BigIntegerField` |
| `motivo` | `CharField(max_length=200)` |
| `occurred_at` / `recorded_at` | `DateTimeField` |
| `clave_idempotencia` | `CharField(max_length=64, unique=True)` |

`CheckConstraint(Q(monto_gs__gt=0), name="sangria_positiva")`; `Index(["sesion"])`.

Ejemplo: `monto_gs=1500000`, `motivo="Traslado a caja fuerte — corte de las 15:00"`.

### 2.5 `orders.SecuenciaTerminal` — numeración por terminal (ADR 0003 §2)

`id UUIDField(pk)`, `terminal OneToOneField(Terminal, PROTECT)`,
`ultimo_numero PositiveIntegerField(default=0)`. Se incrementa con
`select_for_update()`.

### 2.6 `orders.Venta` — RF-3, RF-9, RF-15, RF-27, RF-34, RF-38

| Campo | Tipo | Notas |
|---|---|---|
| `id` | `UUIDField(pk)` | |
| `sesion` | `ForeignKey(SesionCaja, PROTECT, related_name="ventas")` | RF-3, RF-5 |
| `terminal` | `ForeignKey(Terminal, PROTECT)` | |
| `numero_local` | `CharField(max_length=15)` | `001-001-0000431` |
| `tipo` | `CharField(max_length=10, choices=TipoVenta)` | `VENTA` / `ANULACION` |
| `venta_original` | `ForeignKey("self", PROTECT, null=True, blank=True, related_name="anulaciones")` | RF-27 |
| `estado` | `CharField(max_length=10, choices=EstadoVenta)` | `ABIERTA` / `COBRADA` / `ANULADA` |
| `total_gs` | `BigIntegerField(default=0)` | |
| `descuento_total_gs` | `BigIntegerField(default=0)` | |
| `actor` | `ForeignKey(Usuario, PROTECT, related_name="ventas")` | cajero activo por operación (RF-4) |
| `mozo_id` | `UUIDField(null=True, blank=True)` | referencia opaca, entidad en spec 002 (RF-14) |
| `mesa_ref` | `CharField(max_length=20, blank=True)` | ídem |
| `email_cliente` | `EmailField(blank=True)` | RF-17, dato personal → `PRIVACY.md` |
| `nivel_operacion` | `CharField(max_length=2, choices=NivelOperacion)` | nivel vigente al registrar (RF-34..RF-36) |
| `motivo_anulacion` | `CharField(max_length=30, choices=MotivoAnulacion, blank=True)` | lista cerrada RF-26 |
| `occurred_at` / `recorded_at` | `DateTimeField` | RF-38 |
| `clave_idempotencia` | `CharField(max_length=64, unique=True)` | RF-16 |

```python
UniqueConstraint(fields=["terminal", "numero_local"], name="numero_unico_por_terminal")
CheckConstraint(check=Q(total_gs__gte=0), name="total_no_negativo")
CheckConstraint(check=~Q(tipo="ANULACION") | Q(venta_original__isnull=False),
                name="anulacion_referencia_original")                       # RF-27
CheckConstraint(check=~Q(tipo="ANULACION") | ~Q(motivo_anulacion=""),
                name="anulacion_con_motivo")                                # RF-26
Index(fields=["sesion", "estado"]); Index(fields=["recorded_at"])
```

Fila de ejemplo: `numero_local="001-001-0000431"`, `tipo="VENTA"`, `estado="COBRADA"`,
`total_gs=137000`, `descuento_total_gs=0`, `actor=mcabral`, `email_cliente="ana.l@…"`,
`nivel_operacion="N1"`, `occurred_at=2026-09-22T13:41:02-03`,
`recorded_at=2026-09-22T13:41:03-03`,
`clave_idempotencia="vta-CAJA01-1f0c9e3a-2026-09-22"`.

### 2.7 `orders.LineaVenta` — RF-15, RF-25

| Campo | Tipo | Notas |
|---|---|---|
| `id` | `UUIDField(pk)` | |
| `venta` | `ForeignKey(Venta, PROTECT, related_name="lineas")` | |
| `orden` | `PositiveSmallIntegerField` | |
| `producto_id` | `UUIDField(null=True, blank=True)` | sin FK — S1 |
| `descripcion` | `CharField(max_length=120)` | snapshot |
| `cantidad` | `PositiveSmallIntegerField` | |
| `precio_unitario_gs` | `BigIntegerField` | snapshot |
| `descuento_gs` | `BigIntegerField(default=0)` | |
| `total_gs` | `BigIntegerField` | incluye el ajuste de cuadre si es la última vigente |
| `estado` | `CharField(max_length=10, choices=EstadoLinea, default="VIGENTE")` | `VIGENTE` / `ANULADA` |
| `anulada_por` | `ForeignKey(Usuario, PROTECT, null=True, blank=True)` | RF-25 |
| `anulada_en` | `DateTimeField(null=True, blank=True)` | |

```python
UniqueConstraint(fields=["venta", "orden"], name="orden_unico_por_venta")
CheckConstraint(check=Q(cantidad__gt=0), name="cantidad_positiva")
CheckConstraint(check=Q(descuento_gs__gte=0), name="descuento_no_negativo")
```

Ejemplo: `orden=1`, `descripcion="Milanesa napolitana"`, `cantidad=2`,
`precio_unitario_gs=45000`, `descuento_gs=0`, `total_gs=90000`, `estado="VIGENTE"`.

Anular un ítem **no borra la fila**: la pasa a `ANULADA` y dispara `recalcular_totales`.
Es información agregada, no un `UPDATE` destructivo.

### 2.8 `payments.Pago` — RF-8, RF-11, RF-12, RF-13, RF-36

| Campo | Tipo | Notas |
|---|---|---|
| `id` | `UUIDField(pk)` | |
| `venta` | `ForeignKey(Venta, PROTECT, related_name="pagos")` | |
| `sesion` | `ForeignKey(SesionCaja, PROTECT, related_name="pagos")` | |
| `medio` | `CharField(max_length=15, choices=MedioPago)` | `EFECTIVO`, `QR`, `DEBITO`, `CREDITO`, `TRANSFERENCIA` |
| `monto_gs` | `BigIntegerField` | lo efectivamente aplicado a la venta |
| `recibido_gs` | `BigIntegerField(null=True, blank=True)` | solo efectivo: lo que entregó el cliente |
| `vuelto_gs` | `BigIntegerField(default=0)` | vuelto redondeado entregado |
| `ajuste_redondeo_gs` | `BigIntegerField(default=0)` | `vuelto_gs − vuelto_bruto`; puede ser negativo |
| `referencia` | `CharField(max_length=40, blank=True)` | obligatoria si no es efectivo (RF-12) |
| `ultimos_cuatro` | `CharField(max_length=4, blank=True)` | **único** dato de tarjeta almacenable |
| `estado` | `CharField(max_length=25, choices=EstadoPago)` | `ACREDITADO` / `PENDIENTE_CONCILIACION` / `DECLARADO_OFFLINE` |
| `comision_gs` | `BigIntegerField(default=0)` | |
| `acreditacion_estimada` | `DateField(null=True, blank=True)` | |
| `actor` | `ForeignKey(Usuario, PROTECT)` | RF-4 |
| `occurred_at` / `recorded_at` | `DateTimeField` | |
| `clave_idempotencia` | `CharField(max_length=64, unique=True)` | RF-16 |

```python
CheckConstraint(check=Q(monto_gs__gt=0), name="pago_positivo")
CheckConstraint(check=Q(medio="EFECTIVO") | ~Q(referencia=""),
                name="electronico_exige_referencia")                  # RF-12
CheckConstraint(check=~Q(medio="EFECTIVO") | Q(estado="ACREDITADO"),
                name="efectivo_siempre_acreditado")                   # RF-13
CheckConstraint(check=Q(medio="EFECTIVO") | Q(vuelto_gs=0),
                name="sin_vuelto_en_electronico")                     # RF-10
Index(fields=["sesion", "medio"])                                     # RF-32
Index(fields=["estado", "recorded_at"])
```

Ejemplo (efectivo con vuelto, `REDONDEO_VUELTO_GS=500`): `medio="EFECTIVO"`,
`monto_gs=87000`, `recibido_gs=100000`, vuelto bruto `13000` → `vuelto_gs=13000`,
`ajuste_redondeo_gs=0`, `estado="ACREDITADO"`.
Ejemplo (QR offline): `medio="QR"`, `monto_gs=50000`, `referencia="LOTE 0042 / TRX 91183"`,
`estado="DECLARADO_OFFLINE"`, `vuelto_gs=0`.

### 2.9 `payments.Propina` — RF-14

`id UUIDField(pk)`, `venta FK(Venta, PROTECT)`, `monto_gs BigIntegerField`,
`medio CharField(choices=MedioPago)`, `mozo_id UUIDField(null=True)` (referencia opaca,
spec 002), `actor FK(Usuario, PROTECT)`, `occurred_at`/`recorded_at`,
`clave_idempotencia CharField(64, unique=True)`.
`CheckConstraint(Q(monto_gs__gt=0))`. **No** se suma a `Venta.total_gs` ni a las líneas:
es un registro paralelo. Sí entra al efectivo esperado si `medio="EFECTIVO"`, con su
propia línea en el resumen de cierre.

Ejemplo: `monto_gs=15000`, `medio="EFECTIVO"`, `mozo_id=8b1f…`.

### 2.10 `audit.EventoAuditoria` — RF-28, RF-29

| Campo | Tipo | Notas |
|---|---|---|
| `id` | `UUIDField(pk)` | |
| `tipo` | `CharField(max_length=40, choices=TipoEvento)` | `APERTURA_CAJA`, `SANGRIA`, `DESCUENTO_AUTORIZADO`, `ANULACION_ITEM`, `ANULACION_VENTA`, `CIERRE_CAJA`, `SESION_PROLONGADA`, `ALERTA_STOCK_NEGATIVO`, `FALLA_ENVIO_COMPROBANTE` |
| `actor` | `ForeignKey(Usuario, PROTECT, related_name="eventos_como_actor")` | |
| `autorizador` | `ForeignKey(Usuario, PROTECT, null=True, blank=True, related_name="eventos_como_autorizador")` | |
| `autoautorizado` | `BooleanField(default=False)` | RF-29, ADR 0004 |
| `motivo` | `CharField(max_length=30, blank=True)` | código de la lista cerrada |
| `motivo_texto` | `CharField(max_length=200, blank=True)` | detalle libre opcional |
| `objeto_tipo` | `CharField(max_length=40)` | `Venta`, `SesionCaja`, … |
| `objeto_id` | `UUIDField` | sin FK: el log sobrevive a todo |
| `payload` | `JSONField(default=dict)` | montos y contexto, nunca datos de tarjeta |
| `occurred_at` / `recorded_at` | `DateTimeField` | |

```python
CheckConstraint(check=~Q(autoautorizado=True) | Q(autorizador__isnull=False),
                name="autoautorizado_exige_autorizador")
Index(fields=["tipo", "recorded_at"]); Index(fields=["actor", "recorded_at"])
Index(fields=["objeto_tipo", "objeto_id"]); Index(fields=["autoautorizado"])
```

Ejemplo: `tipo="ANULACION_VENTA"`, `actor=mcabral`, `autorizador=rgimenez`,
`autoautorizado=False`, `motivo="ERROR_DE_COBRO"`, `objeto_tipo="Venta"`,
`objeto_id=1f0c…`, `payload={"total_gs":137000,"numero_local":"001-001-0000431"}`.

### 2.11 `sync.RegistroIdempotencia` — RF-16

`id UUIDField(pk)`, `clave CharField(max_length=64, unique=True, db_index=True)`,
`tipo_operacion CharField(40)`, `objeto_id UUIDField(null=True)`,
`respuesta JSONField(default=dict)`, `creado_en DateTimeField`.
Ejemplo: `clave="vta-CAJA01-1f0c9e3a-2026-09-22"`, `tipo_operacion="registrar_cobro"`,
`objeto_id=1f0c…`, `respuesta={"venta_id":"1f0c…","estado":"COBRADA","vuelto_gs":13000}`.

### 2.12 `sync.OperacionEncolada` — RF-37

`id UUIDField(pk)`, `tipo CharField(40)`, `clave_idempotencia CharField(64, unique=True)`,
`payload JSONField`, `estado CharField(choices PENDIENTE/APLICADA/FALLIDA)`,
`intentos PositiveSmallIntegerField(default=0)`, `error_ultimo TextField(blank=True)`,
`origen_terminal FK(Terminal, PROTECT)`, `occurred_at`, `recorded_at`,
`aplicada_en DateTimeField(null=True)`.
`Index(fields=["estado", "recorded_at", "id"])` — ese es el orden de drenado.

### 2.13 `notifications.EnvioComprobante` — RF-18, RF-20

| Campo | Tipo | Notas |
|---|---|---|
| `id` | `UUIDField(pk)` | |
| `venta_id` | `UUIDField(db_index=True)` | sin FK: `notifications` no conoce `orders` |
| `numero_local` | `CharField(max_length=15)` | snapshot para el cuerpo |
| `destinatario` | `EmailField` | dato personal → `PRIVACY.md` |
| `asunto` | `CharField(max_length=140)` | |
| `cuerpo_datos` | `JSONField(default=dict)` | datos ya renderizables, sin tarjeta |
| `estado` | `CharField(max_length=12, choices=EstadoEnvio)` | `PENDIENTE` / `ENVIANDO` / `ENVIADO` / `FALLIDO` |
| `intentos` | `PositiveSmallIntegerField(default=0)` | |
| `proveedor` | `CharField(max_length=20, blank=True)` | `SES`, `CONSOLA` |
| `mensaje_id` | `CharField(max_length=120, blank=True)` | id del proveedor |
| `error_ultimo` | `TextField(blank=True)` | |
| `encolado_en` / `enviado_en` | `DateTimeField` / `(null=True)` | |
| `clave_idempotencia` | `CharField(max_length=64, unique=True)` | evita reenvíos duplicados |

`Index(fields=["estado", "encolado_en"])`.
Ejemplo: `destinatario="ana.lopez@gmail.com"`, `estado="PENDIENTE"`, `intentos=2`,
`error_ultimo="Throttling: Maximum sending rate exceeded"`,
`encolado_en=2026-09-22T13:41:03-03`, `enviado_en=None`.

---

## 3. Algoritmos en pseudocódigo

### 3.1 Redondeo y cuadre de líneas (`shared/money.py`) — RF-7, RF-15

```
función redondear_gs(monto: int, multiplo: int) -> int:
    si multiplo <= 1: devolver monto
    resto = monto mod multiplo                  # mod de Python: siempre >= 0
    si resto * 2 >= multiplo:                   # redondeo comercial, mitad hacia arriba
        devolver monto - resto + multiplo
    devolver monto - resto

función cuadrar_lineas(total_objetivo: int, totales_linea: list[int]) -> list[int]:
    # ADR 0002: se redondea el TOTAL y se ajusta la ÚLTIMA línea. Nunca al revés.
    si totales_linea está vacía:
        invariante total_objetivo == 0
        devolver []
    suma = sum(totales_linea)
    diferencia = total_objetivo - suma
    ajustadas = copia(totales_linea)
    ajustadas[-1] += diferencia
    invariante sum(ajustadas) == total_objetivo         # RF-15, se asegura en test
    invariante ajustadas[-1] >= 0                        # si no, es un error de datos
    devolver ajustadas
```

### 3.2 Cálculo del vuelto (`domain/vuelto.py`) — RF-11

El punto no obvio: redondear el vuelto **descuadra la caja** si no se registra. El ajuste
se guarda explícitamente y entra al arqueo, si no el cierre nunca cuadraría.

```
función calcular_vuelto(excedente_efectivo: int, redondeo_gs: int) -> Vuelto:
    si excedente_efectivo <= 0:
        devolver Vuelto(bruto=0, entregado=0, ajuste=0)
    entregado = redondear_gs(excedente_efectivo, redondeo_gs)
    ajuste    = entregado - excedente_efectivo     # >0: la caja entrega de más
    devolver Vuelto(bruto=excedente_efectivo, entregado=entregado, ajuste=ajuste)

# Ejemplo con REDONDEO_VUELTO_GS = 500:
#   excedente 13.000 -> entregado 13.000, ajuste 0
#   excedente 13.300 -> entregado 13.500, ajuste +200   (la caja queda 200 corta)
#   excedente 13.200 -> entregado 13.000, ajuste -200   (la caja queda 200 larga)
```

### 3.3 Asignación de pago mixto (`domain/cobro.py`) — RF-8, RF-9, RF-10, RF-11

```
función asignar_pagos(total_gs, pagos_solicitados, redondeo_gs) -> Asignacion:
    # 1. Validación previa: lo electrónico no puede exceder el total (RF-10)
    no_efectivo = suma(p.monto for p in pagos_solicitados si p.medio != EFECTIVO)
    si no_efectivo > total_gs:
        lanzar ExcesoNoEfectivo(exceso = no_efectivo - total_gs)

    # 2. Referencia obligatoria en todo medio electrónico (RF-12)
    para p en pagos_solicitados donde p.medio != EFECTIVO:
        si p.referencia está vacía: lanzar ReferenciaRequerida(p.medio)

    # 3. Lo electrónico se aplica íntegro primero: nunca genera vuelto
    saldo = total_gs
    aplicados = []
    para p en pagos_solicitados donde p.medio != EFECTIVO (en orden de ingreso):
        aplicados.append(Aplicado(p, monto=p.monto, vuelto=0, ajuste=0))
        saldo -= p.monto

    # 4. El efectivo cubre el saldo; el sobrante se acumula para UN solo vuelto
    excedente = 0
    para p en pagos_solicitados donde p.medio == EFECTIVO (en orden de ingreso):
        aplicado  = min(p.monto, max(saldo, 0))
        excedente += p.monto - aplicado
        saldo     -= aplicado
        aplicados.append(Aplicado(p, monto=aplicado, recibido=p.monto))

    # 5. Un único vuelto, sobre el último pago en efectivo (RF-11)
    vuelto = calcular_vuelto(excedente, redondeo_gs)
    si vuelto.entregado > 0:
        último_efectivo(aplicados).vuelto = vuelto.entregado
        último_efectivo(aplicados).ajuste = vuelto.ajuste

    # 6. Estado resultante (RF-9)
    si saldo > 0:
        devolver Asignacion(estado=ABIERTA, saldo_pendiente=saldo, aplicados, vuelto)
    devolver Asignacion(estado=COBRADA, saldo_pendiente=0, aplicados, vuelto)
```

Caso límite cubierto: un pago 100% efectivo sobre una venta ya parcialmente pagada; y un
mixto cuyas partes no suman (deja la venta ABIERTA con saldo, no rechaza).

### 3.4 Registro del cobro (`payments/services/cobro.py`) — orquestador

```
función registrar_cobro(venta_id, pagos, email_cliente, propina, clave_idempotencia,
                        occurred_at, actor, clock, proveedor_stock, config):

  devolver ejecutar_idempotente(clave_idempotencia, "registrar_cobro", fn=lambda:      # RF-16

    con transaction.atomic():
        venta   = Venta.objects.select_for_update().get(id=venta_id)
        sesion  = SesionCaja.objects.select_for_update().get(                           # candado
                      terminal=venta.terminal, estado=ABIERTA)  o  lanzar SinSesion     # RF-5
        exigir_rol(actor, CAJERO)                                                       # servicio, no vista

        nivel = nivel_actual(sondas, clock)                                             # RF-34
        asignacion = asignar_pagos(venta.total_gs, pagos, config.REDONDEO_VUELTO_GS)

        para aplicado en asignacion.aplicados:
            estado_pago = ACREDITADO si aplicado.medio == EFECTIVO                      # RF-13
                          sino (DECLARADO_OFFLINE si nivel != N0 else PENDIENTE_CONCILIACION)  # RF-12, RF-36
            crear Pago(..., occurred_at=occurred_at, recorded_at=clock.now(),           # RF-38
                       estado=estado_pago, clave_idempotencia=derivar(clave, i))

        si propina: crear Propina(...)                                                  # RF-14

        venta.estado = asignacion.estado
        venta.nivel_operacion = nivel
        venta.recorded_at = clock.now()
        si asignacion.estado == COBRADA y email_cliente:
            venta.email_cliente = email_cliente                                         # RF-17
        venta.save()

        si asignacion.estado == COBRADA y email_cliente:
            envio_id = encolar_comprobante(dto(venta), email_cliente, clock)            # RF-18
        # si NO hay email: no se encola nada y el cobro se completa igual               # RF-19

    # --- fuera del atomic: nada de acá puede revertir la venta --------------------
    si envio_id: notifications.tasks.enviar_comprobante.delay(envio_id)                 # RF-18, RF-20
    intentar:
        aviso = proveedor_stock.descontar_por_venta(dto(venta))
        si aviso: registrar_evento(ALERTA_STOCK_NEGATIVO, ...)                          # RF-39
    capturar cualquier excepción como e:
        registrar_evento(ALERTA_STOCK_NEGATIVO, payload={"error": str(e)})              # RF-39

    devolver ResultadoCobro(venta_id, estado, saldo_pendiente, vuelto_entregado)
  )
```

Invariante de disponibilidad: entre el `commit` y el `return` no hay ninguna llamada que
pueda hacer fallar el cobro. Ni correo, ni stock, ni sync.

### 3.5 Autorización con PIN (`accounts/services/autorizacion.py`) — RF-23, RF-26, RF-28, RF-29

```
función verificar_pin_supervisor(pin, supervisor_id, actor, motivo, clock) -> Autorizacion:
    supervisor = Usuario.objects.select_for_update().get(id=supervisor_id)
    si supervisor.pin_bloqueado_hasta y supervisor.pin_bloqueado_hasta > clock.now():
        lanzar PinBloqueado
    si SUPERVISOR no en roles(supervisor): lanzar NoAutorizado
    si no check_password(pin, supervisor.pin_hash):
        supervisor.pin_intentos_fallidos += 1
        si intentos >= 5: supervisor.pin_bloqueado_hasta = clock.now() + 5 min
        guardar; lanzar PinInvalido
    supervisor.pin_intentos_fallidos = 0; guardar
    devolver Autorizacion(autorizador=supervisor, motivo=motivo,
                          autoautorizado=(supervisor.id == actor.id),         # RF-29
                          en=clock.now())
```

Todo servicio que requiere elevación recibe `autorizacion: Autorizacion` **ya
construida** y verifica `autorizacion is not None`. La vista no puede fabricarla: el único
constructor válido está en este servicio. Es lo que hace imposible autorizar desde el
template (constitución §4).

### 3.6 Descuentos — RF-22, RF-23, RF-24

```
función evaluar_descuento(monto_gs, base_gs, tope_pct, tope_gs, autorizacion) -> Veredicto:
    si autorizacion no es nulo:
        devolver ACEPTADO_POR_AUTORIZACION      # el supervisor no tiene tope (RF-24)
    tope_efectivo = min(base_gs * tope_pct // 100, tope_gs)   # entero, sin Decimal
    si monto_gs <= tope_efectivo: devolver LIBRE              # RF-22 (el tope exacto pasa)
    devolver REQUIERE_PIN                                     # RF-23
```

Caso límite de la spec: descuento exactamente en el tope → `LIBRE`; uno más →
`REQUIERE_PIN`. La división entera `// 100` es el único redondeo de porcentaje y va hacia
abajo, siempre en contra del descuento.

### 3.7 Conteo ciego y cierre (`cash/services/arqueo.py`) — RF-30, RF-31, RF-32

El conteo se **persiste antes** de calcular el esperado. Si el cálculo se hiciera primero,
cualquier bug o log filtraría el monto esperado y el control dejaría de ser ciego.

```
función iniciar_cierre(sesion_id, actor) -> PantallaConteo:
    exigir_rol(actor, CAJERO o SUPERVISOR)
    # devuelve SOLO los campos del formulario. Nunca el esperado. Nunca el total de ventas.
    devolver PantallaConteo(sesion_id, denominaciones=DENOMINACIONES_GS)        # RF-30

función registrar_conteo(sesion_id, contado_gs, pin, supervisor_id, actor, clock):
    autorizacion = verificar_pin_supervisor(pin, supervisor_id, actor,
                                            motivo="CIERRE_DE_CAJA", clock)     # RF-31
    con transaction.atomic():
        sesion = SesionCaja.objects.select_for_update().get(id=sesion_id, estado=ABIERTA)
        sesion.efectivo_contado_gs = contado_gs           # 1) se guarda el conteo
        sesion.save()

        # 2) recién ahora se calcula el esperado
        efectivo   = payments.selectors.total_efectivo(sesion)      # solo EFECTIVO (RF-13)
        vueltos    = payments.selectors.total_vuelto(sesion)
        ajustes    = payments.selectors.total_ajuste_redondeo(sesion)
        propinas   = payments.selectors.total_propina_efectivo(sesion)
        sangrias   = suma(sesion.sangrias.monto_gs)
        esperado   = sesion.fondo_inicial_gs + efectivo + propinas - vueltos - sangrias
        # nota: 'vueltos' ya es el vuelto REDONDEADO entregado, por eso el ajuste
        #       de redondeo no se resta otra vez; se reporta aparte en el resumen.

        sesion.efectivo_esperado_gs = esperado
        sesion.diferencia_gs        = contado_gs - esperado          # >0 sobrante, <0 faltante
        sesion.estado               = CERRADA
        sesion.supervisor_cierre    = autorizacion.autorizador
        sesion.cerrada_occurred_at  = occurred_at
        sesion.cerrada_recorded_at  = clock.now()
        sesion.save()
        registrar_evento(CIERRE_CAJA, actor, autorizacion, sesion,
                         payload={"esperado": esperado, "contado": contado_gs,
                                  "diferencia": sesion.diferencia_gs,
                                  "ajuste_redondeo": ajustes})                   # RF-28

    devolver resumen_de_cierre(sesion)          # fondo, ventas por medio, sangrías,
                                                # esperado, contado, diferencia (RF-32)
```

### 3.8 Idempotencia y replay de la cola offline — RF-16, RF-37

```
función ejecutar_idempotente(clave, tipo, fn):
    con transaction.atomic():
        registro, creado = RegistroIdempotencia.objects.select_for_update()\
                              .get_or_create(clave=clave, defaults={"tipo_operacion": tipo})
        si no creado:
            devolver registro.respuesta          # el resultado de la PRIMERA vez (RF-16)
        resultado = fn()
        registro.objeto_id = resultado.id
        registro.respuesta = serializar(resultado)
        registro.save()
        devolver resultado

función drenar(limite, clock):
    # Orden estable: recorded_at es el reloj del SERVIDOR al encolar, monótono por
    # terminal. occurred_at (reloj del dispositivo) NO se usa para ordenar: miente.
    pendientes = OperacionEncolada.objects\
        .filter(estado=PENDIENTE).order_by("recorded_at", "id")[:limite]
    para op en pendientes:
        intentar:
            resultado = despachar(op.tipo, op.payload, op.clave_idempotencia)   # idempotente
            op.estado = APLICADA; op.aplicada_en = clock.now()
        capturar ErrorPermanente as e:
            op.estado = FALLIDA; op.error_ultimo = str(e)
            registrar_evento(FALLA_SYNC, ...)
        capturar ErrorTransitorio as e:
            op.intentos += 1; op.error_ultimo = str(e)       # queda PENDIENTE, reintenta
        guardar op
```

Caso límite de la spec (la misma operación llegando dos veces): la segunda entra a
`ejecutar_idempotente`, encuentra el registro, devuelve la respuesta original y **no**
crea una segunda venta.

### 3.9 Envío del comprobante — RF-18, RF-19, RF-20

```
función encolar_comprobante(venta_dto, email, clock) -> uuid:          # dentro del atomic
    si email está vacío o es inválido: devolver nulo                    # RF-19
    envio = EnvioComprobante.objects.create(
        venta_id=venta_dto.id, numero_local=venta_dto.numero_local,
        destinatario=email, estado=PENDIENTE, encolado_en=clock.now(),
        cuerpo_datos=datos_renderizables(venta_dto),   # sin tarjeta, sin PIN
        clave_idempotencia=f"cmp-{venta_dto.id}")
    devolver envio.id

tarea despachar(envio_id, proveedor, clock):                            # Celery, nunca síncrono
    envio = EnvioComprobante.objects.select_for_update().get(id=envio_id)
    si envio.estado == ENVIADO: devolver                                # idempotente
    envio.estado = ENVIANDO; envio.intentos += 1; guardar
    resultado = proveedor.enviar(MensajeCorreo(destinatario, asunto, cuerpo))
    si resultado.ok:
        envio.estado = ENVIADO; envio.mensaje_id = resultado.mensaje_id
        envio.enviado_en = clock.now()
    sino si resultado.reintentable:                                     # sin internet, throttling
        envio.estado = PENDIENTE; envio.error_ultimo = resultado.error
        reintentar con backoff exponencial (1m, 5m, 15m, 1h, 6h), tope 8 intentos   # RF-20
    sino:                                                               # dominio no verificado, rebote duro
        envio.estado = FALLIDO; envio.error_ultimo = resultado.error
        registrar_evento(FALLA_ENVIO_COMPROBANTE, payload={...})        # nunca falla en silencio
    guardar envio
```

`reintentar_pendientes()` (Celery beat, cada 10 min) recoge los `PENDIENTE` con
`encolado_en` viejo: es la red de seguridad para el caso "corte de energía entre el cobro
y el envío" de la spec.

### 3.10 Nivel de degradación (`sync/services/nivel.py`) — RF-34

```
función nivel_actual(sondas, clock) -> NivelOperacion:
    si no sondas.edge_box_responde():   devolver N3
    si no sondas.lan_viva():            devolver N2
    si no sondas.internet():            devolver N1
    devolver N0
    # N4 (sin energía) no es observable por el sistema: queda fuera de alcance en 001.
```

El resultado se cachea 5 segundos en Redis: se consulta en cada render de la pantalla de
caja y no puede costar una llamada de red por request.

### 3.11 Alerta de sesión prolongada (`cash/tasks.py`) — RF-33

```
tarea alertar_sesiones_prolongadas(clock, horas_limite):
    para sesion en SesionCaja.filter(estado=ABIERTA, alerta_prolongada_emitida=False):
        si sesion_prolongada(sesion.abierta_recorded_at, clock.now(), horas_limite):
            registrar_evento(SESION_PROLONGADA, actor=sesion.cajero_apertura,
                             objeto=sesion, payload={"horas": …})
            sesion.alerta_prolongada_emitida = True; guardar
```

Se compara contra `abierta_recorded_at` (reloj del servidor), no contra `occurred_at`: un
dispositivo con el reloj adelantado no debe disparar ni suprimir la alerta.

---

## 4. Decisiones técnicas

Cada decisión con la alternativa que se descartó y por qué.

**D1 — `notifications/` es una app nueva, no un módulo dentro de `cash` o `payments`.**
Tiene modelo propio (`EnvioComprobante`, con su ciclo de vida y sus reintentos), un puerto
a un tercero, y una razón de cambio independiente de la caja: cambiar de SES a Postmark no
es un cambio de caja. Es exactamente el criterio con el que `ARCHITECTURE.md` §3 separa
los contextos, y el `stack.md` aprobado ya la nombra por ruta
(`notifications/providers/base.py`).
*Descartado:* `payments/notifications/`. Acoplaría el ciclo de vida del correo a la app que
tiene el candado de dinero y obligaría a `payments` a conocer estados de envío, bounces y
reintentos. La app de caja debe saber solo que "hay un comprobante pendiente".
*Consecuencia:* `ARCHITECTURE.md` §3 hay que actualizarlo (S3).

**D2 — `Venta` y `LineaVenta` viven en `orders/`, no en `payments/`.**
La venta es el documento; el pago es un hecho sobre ese documento. Con la venta en
`orders`, la dependencia es `payments -> orders` y nunca circular; spec 002 extiende el
mismo modelo con mesa, mozo y comanda sin migrar nada.
*Descartado:* `Venta` en `payments`. Habría forzado `orders -> payments` en spec 002 y
dejado dos apps escribiendo sobre la misma tabla.

**D3 — Anular un ítem cambia `LineaVenta.estado` a `ANULADA`; no borra la fila.**
Conserva qué se cargó, quién lo sacó y cuándo — el patrón que un cajero usa para tapar un
faltante es justamente cargar y descargar ítems.
*Descartado:* `DELETE` de la línea mientras la venta está abierta. Es más simple y destruye
la evidencia; contradice ADR 0003 §3.
*Descartado también:* `deleted_at` (soft delete). ADR 0003 ya lo rechazó por permitir
`UPDATE` sobre el original sin rastro; el par `estado` + `anulada_por` + `anulada_en` agrega
información en vez de tacharla.

**D4 — El ajuste de redondeo del vuelto se persiste como campo (`Pago.ajuste_redondeo_gs`).**
Redondear el vuelto mueve dinero real. Sin registrarlo, toda sesión con vueltos redondeados
cerraría con una diferencia inexplicable y el arqueo perdería su valor como control.
*Descartado:* recalcularlo al cierre desde `recibido_gs - monto_gs - vuelto_gs`. Es
derivable, sí, pero obliga a recorrer todos los pagos para explicar una diferencia y se
rompe apenas cambie `REDONDEO_VUELTO_GS` a mitad de un turno.

**D5 — La `Autorizacion` es un value object que solo `accounts/services/autorizacion.py`
puede construir, y los servicios elevados lo exigen como parámetro.**
Hace estructuralmente imposible que un endpoint autorice sin verificar el PIN: no hay
camino desde la vista a un `Autorizacion` válido.
*Descartado:* pasar `pin: str` a cada servicio y verificarlo adentro. Multiplica la
verificación por N servicios, y cada copia es una oportunidad de olvidar el bloqueo por
intentos o la marca de `autoautorizado`.

**D6 — El conteo se persiste antes de calcular el esperado (§3.7).**
El arqueo ciego es un control de fraude: si el esperado existe en memoria antes del conteo,
basta un log, un mensaje de error o una plantilla descuidada para filtrarlo.
*Descartado:* calcular el esperado al entrar a la pantalla de cierre y compararlo al
recibir el conteo. Es el orden natural de escribir el código y es exactamente el que
rompe el control.

**D7 — El envío del comprobante se dispara con `transaction.on_commit` + Celery, nunca
síncrono.**
El NFR de <500 ms no admite esperar una respuesta HTTP externa, y la constitución §1 prohíbe
que un tercero pueda bloquear un cobro.
*Descartado:* `EMAIL_BACKEND` síncrono de Django en la vista. Es una línea de código y ata
el cobro a la latencia de AWS (ya descartado en el `stack.md` como candidato A).

**D8 — No se crea `payments/gateways/` en esta spec.**
Bancard está fuera de alcance y no hay documentación en mano (AGENTS §0.5). Un puerto sin
implementación es abstracción prematura (anti-objetivos).
*Descartado:* dejar el puerto "listo para cuando llegue". Sin la documentación del
proveedor, la forma del puerto sería inventada, que es el modo de falla más caro del
proyecto.

**D9 — El log de auditoría se protege con permisos de PostgreSQL, no solo con código.**
Una migración hace `REVOKE UPDATE, DELETE` sobre la tabla para el rol de aplicación. Un
control que el ORM puede saltear con `.update()` no es un control (constitución §3).
*Descartado:* solo sobrescribir `delete()` y `save()` en el modelo. Un `queryset.update()`
o un `raw` lo esquivan sin esfuerzo.

**D10 — Un solo vuelto por cobro, asignado al último pago en efectivo.**
El cliente recibe un vuelto, no uno por billete. Asignarlo al último pago en efectivo
mantiene la invariante `recibido - monto = vuelto + ajuste` por fila.
*Descartado:* prorratear el vuelto entre los pagos en efectivo. No corresponde a nada
físico y complica la explicación de una diferencia de arqueo.

**D11 — El orden de drenado de la cola usa `recorded_at` (servidor) + `id`, no
`occurred_at` (dispositivo).**
Los relojes de los dispositivos mienten (ADR 0003 §5); un reloj adelantado reordenaría
operaciones ajenas. `occurred_at` se conserva porque es el dato del negocio, pero no
gobierna el orden de aplicación.
*Descartado:* ordenar por `occurred_at`. Es el orden "real" percibido y es inestable ante
el caso límite que la propia spec enumera (reloj adelantado y atrasado).

**D12 — Sin cadena de hashes en el log de auditoría.**
`REVOKE` + append-only + réplica a la nube cubren el requisito de la spec. Una cadena de
hashes exige gestión de claves y verificación periódica para tener sentido real.
*Descartado (pospuesto):* encadenar `hash_anterior`/`hash`. Vale cuando exista la spec de
facturación electrónica y un requisito de no repudio; hoy sería ceremonia.

**D13 — `RelojFijo` inyectado por parámetro en lugar de congelar el tiempo globalmente.**
Cada servicio recibe `clock` y nunca llama a `timezone.now()`. Un test puede correr el
reloj sin afectar a otros tests ni depender de una librería de parcheo.
*Descartado:* `freezegun` / parcheo de `timezone.now`. Funciona, pero deja `now()` dentro de
la lógica, y basta que alguien agregue una llamada nueva para que un test deje de ser
determinístico sin que nadie lo note.

---

## 5. Estrategia de test

### 5.1 Qué se inyecta (esto es lo que hace determinístico al sistema)

| Dependencia | Puerto | Doble de test |
|---|---|---|
| **Tiempo** | `shared/clock.py::Clock` | `RelojFijo(instante)`, `RelojAvanzable` |
| Generación de UUID | `shared/ids.py::GeneradorUuid` | `UuidSecuencial` |
| Correo | `notifications/providers/base.py::ProveedorCorreo` | `ProveedorEnMemoria` (con `forzar_fallo(reintentable=…)`) |
| Stock | `inventory/services/stock.py` | `StockQueExplota`, `StockNoOp` |
| Nivel de operación | `sync/services/nivel.py::Sondas` | `SondasFijas(internet=False, lan=True, edge=True)` |
| Configuración | `settings` | `override_settings(REDONDEO_VUELTO_GS=500, …)` |

**El reloj ante todo:** `timezone.now()` no aparece en ningún módulo de `src/domain`,
`src/shared` ni `*/services/*`. Se verifica con un test de arquitectura
(`tests/unit/test_arquitectura.py`) que hace grep de AST sobre esos paquetes y falla si
encuentra la llamada. Lo mismo para `import django` dentro de `src/domain` y para
`decimal.Decimal` en cualquier lado (esto último ya lo cubre ruff `TID`).

### 5.2 Tipo de test por RF

| Tipo | Corre contra | Qué cubre | RF |
|---|---|---|---|
| **Unitario de dominio** (`tests/unit/`) — sin BD, sin Django | funciones puras | redondeo, cuadre, vuelto, asignación mixta, topes de descuento, esperado/diferencia de arqueo, sesión prolongada | RF-7, RF-9, RF-10, RF-11, RF-13, RF-15, RF-22, RF-23, RF-24, RF-31, RF-33 |
| **Integración de servicio** (`tests/integration/`) — PostgreSQL real, marker `integration` | servicios + modelos | constraints, candados, idempotencia, append-only, auditoría, arqueo, cola, envío | RF-1..RF-6, RF-8, RF-12, RF-14, RF-16..RF-20, RF-25..RF-32, RF-35..RF-39 |
| **Test de constraint** (integración) | la BD, no el ORM | que `IntegrityError` salte aunque el servicio tenga un bug: sesión doble, referencia vacía, efectivo no acreditado, anulación sin original | RF-2, RF-12, RF-13, RF-27 |
| **Test de arquitectura** (unitario) | AST de `src/` | sin `now()` en servicios/dominio, sin Django en `domain`, sin import de modelos entre apps, cobro no bloqueante | RF-39 + invariantes del plan |
| **Vista/plantilla** (integración) | cliente de test de Django | nivel visible en toda pantalla de caja, mensaje de factura no disponible, conteo sin esperado en el contexto | RF-21, RF-30, RF-34 |
| **E2E** (`tests/e2e/`, marker `e2e`, solo `make ship`) | flujo completo | los dos escenarios de "Criterios de finalización" de la spec | RF-1..RF-39 (humo) |

### 5.3 Tests que existen antes que cualquier otra cosa

ADR 0002 lo exige: `tests/unit/shared/test_money.py` y `tests/unit/domain/test_vuelto.py`
se escriben y pasan antes de que exista un solo cálculo que los use. Aserciones exactas
(`assert vuelto.entregado == 13_500`); `approx` sobre dinero está prohibido.

### 5.4 Casos límite de la spec → test nominal

| Caso límite | Test |
|---|---|
| Pago exacto / de más / de menos | `test_cobro.py::test_pago_exacto`, `::test_pago_con_vuelto`, `::test_pago_parcial_deja_venta_abierta` |
| Mixto que suma y que no suma | `test_cobro_mixto.py::test_mixto_exacto`, `::test_mixto_incompleto` |
| Vuelto no múltiplo del redondeo | `test_vuelto.py::test_vuelto_redondea_y_registra_ajuste` |
| Descuento en el tope, uno menos, uno más | `test_descuentos.py::test_tope_exacto_no_pide_pin` (+2) |
| Anular una venta ya anulada | `test_anulacion.py::test_doble_anulacion_rechazada` |
| Misma operación dos veces desde la cola | `test_idempotencia.py::test_replay_no_duplica_venta` |
| Reloj adelantado / atrasado | `test_cola.py::test_orden_ignora_reloj_del_dispositivo` |
| Dos terminales sobre la misma mesa | `test_cobro.py::test_select_for_update_serializa_dos_cobros` |
| Arqueo con sobrante / faltante / exacto | `test_arqueo.py` (3 casos) |
| Cajero que abandona el turno | `test_alerta_sesion.py::test_alerta_a_las_8_horas` |
| Corte entre cobro y envío | `test_comprobante.py::test_reintento_tras_fallo_transitorio` |
| Cliente pide factura formal | `test_vistas_cobro.py::test_mensaje_factura_no_disponible` |
| Email con formato inválido | `test_comprobante.py::test_email_invalido_no_bloquea_el_cobro` |

---

## 6. Archivos declarados por área de tarea

El bucle de construcción abre **solo** los archivos de su área. Las áreas están en orden de
dependencia: A antes que B, y así.

### Área A — Cimientos (RF-7, RF-11, RF-15)
```
src/shared/money.py            src/shared/clock.py         src/shared/ids.py
src/shared/result.py           src/shared/errors.py        src/shared/mensajes.py
src/domain/enums.py            src/domain/errores.py
tests/unit/shared/test_money.py            tests/unit/shared/test_clock.py
tests/unit/test_arquitectura.py
```

### Área B — Dominio puro del cobro (RF-8..RF-11, RF-13, RF-15, RF-22..RF-24, RF-30..RF-33)
```
src/domain/cobro.py     src/domain/vuelto.py     src/domain/venta.py
src/domain/descuentos.py  src/domain/arqueo.py   src/domain/disponible.py
src/domain/sesion.py
tests/unit/domain/test_cobro.py        tests/unit/domain/test_vuelto.py
tests/unit/domain/test_venta.py        tests/unit/domain/test_descuentos.py
tests/unit/domain/test_arqueo.py       tests/unit/domain/test_sesion.py
```

### Área C — Cuentas, roles y PIN (RF-23, RF-26, RF-28, RF-29, RF-31)
```
src/accounts/models.py      src/accounts/migrations/0001_initial.py
src/accounts/services/autorizacion.py   src/accounts/services/permisos.py
src/accounts/selectors.py   src/accounts/admin.py   src/accounts/apps.py
src/config/settings/base.py  (AUTH_USER_MODEL)
tests/integration/accounts/test_autorizacion.py
tests/integration/accounts/test_permisos.py
tests/factories/accounts.py
```

### Área D — Auditoría (RF-28, RF-29)
```
src/audit/models.py    src/audit/services/registro.py    src/audit/selectors.py
src/audit/apps.py      src/audit/migrations/0001_initial.py
src/audit/migrations/0002_revocar_permisos.py
tests/integration/audit/test_registro.py
tests/integration/audit/test_inmutabilidad.py
tests/factories/audit.py
```

### Área E — Sesión de caja y sangría (RF-1..RF-6, RF-33)
```
src/cash/models.py      src/cash/migrations/0001_initial.py    src/cash/apps.py
src/cash/services/sesion.py     src/cash/services/sangria.py
src/cash/tasks.py       src/cash/forms.py       src/cash/views/sesion.py
src/cash/templates/cash/apertura.html   src/cash/templates/cash/panel.html
src/cash/templates/cash/sangria.html
src/config/urls.py      src/config/celery.py
tests/integration/cash/test_sesion.py     tests/integration/cash/test_sangria.py
tests/integration/cash/test_alerta_sesion.py
tests/factories/cash.py
```

### Área F — Idempotencia, cola y niveles (RF-16, RF-34..RF-38)
```
src/sync/models.py       src/sync/migrations/0001_initial.py   src/sync/apps.py
src/sync/services/idempotencia.py   src/sync/services/cola.py   src/sync/services/nivel.py
src/sync/context_processors.py      src/sync/tasks.py
src/cash/templates/cash/_nivel_operacion.html
tests/integration/sync/test_idempotencia.py    tests/integration/sync/test_cola.py
tests/unit/sync/test_nivel.py
tests/factories/sync.py
```

### Área G — Venta, líneas, numeración, descuentos, anulación de ítem (RF-15, RF-22..RF-25, RF-38)
```
src/orders/models.py    src/orders/migrations/0001_initial.py   src/orders/apps.py
src/orders/services/venta.py       src/orders/services/numeracion.py
src/orders/services/descuento.py   src/orders/services/anulacion_item.py
src/orders/views/venta.py
src/orders/templates/orders/venta_abierta.html
src/orders/templates/orders/_lineas.html
src/orders/templates/orders/_descuento_pin.html
tests/integration/orders/test_venta.py       tests/integration/orders/test_numeracion.py
tests/integration/orders/test_descuento.py   tests/integration/orders/test_anulacion_item.py
tests/factories/orders.py
```

### Área H — Cobro, pagos y propina (RF-8..RF-14, RF-16, RF-35, RF-36, RF-39)
```
src/payments/models.py    src/payments/migrations/0001_initial.py   src/payments/apps.py
src/payments/services/cobro.py     src/payments/services/propina.py
src/payments/selectors.py   src/payments/messages.py   src/payments/forms.py
src/payments/views/cobro.py
src/payments/templates/payments/cobro.html
src/payments/templates/payments/_pago_linea.html
src/payments/templates/payments/_vuelto.html
src/payments/templates/payments/_pin_supervisor.html
src/payments/templates/payments/_factura_no_disponible.html
src/inventory/services/stock.py    src/inventory/apps.py
tests/integration/payments/test_cobro.py      tests/integration/payments/test_cobro_mixto.py
tests/integration/payments/test_propina.py    tests/integration/payments/test_offline.py
tests/integration/payments/test_stock_no_bloquea.py
tests/factories/payments.py
```

### Área I — Anulación de venta cobrada (RF-26, RF-27, RF-28, RF-29)
```
src/payments/services/anulacion_venta.py   src/payments/views/anulacion.py
src/payments/templates/payments/anulacion.html
tests/integration/payments/test_anulacion.py
```

### Área J — Comprobante por correo (RF-17..RF-21)
```
src/notifications/models.py    src/notifications/migrations/0001_initial.py
src/notifications/apps.py
src/notifications/providers/base.py     src/notifications/providers/ses.py
src/notifications/providers/consola.py  src/notifications/providers/memoria.py
src/notifications/services/comprobante.py     src/notifications/tasks.py
src/notifications/templates/notifications/comprobante.html
src/notifications/templates/notifications/comprobante.txt
src/payments/forms.py (EmailComprobanteForm)
src/payments/templates/payments/_email_comprobante.html
src/config/settings/base.py (PROVEEDOR_CORREO, REMITENTE_COMPROBANTE)
tests/integration/notifications/test_comprobante.py
tests/integration/notifications/test_reintentos.py
tests/factories/notifications.py
```

### Área K — Arqueo y cierre (RF-30, RF-31, RF-32)
```
src/cash/services/arqueo.py    src/cash/services/resumen.py
src/cash/views/cierre.py       src/cash/forms.py (ConteoForm)
src/cash/templates/cash/conteo_ciego.html
src/cash/templates/cash/resumen_cierre.html
tests/integration/cash/test_arqueo.py    tests/integration/cash/test_resumen.py
tests/integration/cash/test_conteo_ciego.py
```

### Área L — E2E y documentación de cierre
```
tests/e2e/test_flujo_caja.py        tests/e2e/test_flujo_degradado.py
tests/conftest.py
docs/ARCHITECTURE.md   (agregar `notifications/` a §3 — S3)
docs/PRIVACY.md        (email del cliente: finalidad, retención, base legal)
docs/DEPLOYMENT.md     (dominio verificado, SPF/DKIM/DMARC, acceso de producción SES)
specs/001-caja-y-cobros/validation.md
```

**Tareas de infraestructura previas a J**, fuera del código (del `stack.md`): verificar el
dominio propio en SES y solicitar el acceso de producción con 24-48 h de margen. Mientras
SES esté en sandbox, `PROVEEDOR_CORREO=CONSOLA` en desarrollo y solo direcciones
verificadas en la demo.

---

## 7. Cobertura de RF

Todo RF tiene al menos un módulo y un test. Un RF sin cobertura bloquea la aprobación.

| RF | Módulo responsable | Test |
|---|---|---|
| RF-1 | `cash/services/sesion.py::abrir_sesion` | `integration/cash/test_sesion.py::test_apertura_registra_fondo_terminal_actor_y_tiempos` |
| RF-2 | `cash/models.py` (`unica_sesion_abierta_por_terminal`) + `sesion.py` | `test_sesion.py::test_segunda_apertura_rechazada_informa_sesion_vigente` + `::test_constraint_bloquea_sesion_doble` |
| RF-3 | `cash/services/sesion.py::exigir_sesion_abierta` | `test_sesion.py::test_operaciones_se_registran_contra_sesion_abierta` |
| RF-4 | `orders.Venta.actor`, `payments.Pago.actor` | `test_sesion.py::test_cajero_distinto_opera_sin_reabrir_sesion` |
| RF-5 | `payments/services/cobro.py` (guard `SinSesion`) | `integration/payments/test_cobro.py::test_cobro_sin_sesion_rechazado` |
| RF-6 | `cash/services/sangria.py` | `integration/cash/test_sangria.py::test_sangria_descuenta_y_registra_motivo_y_actor` |
| RF-7 | `shared/money.py`, todos los `BigIntegerField` | `unit/shared/test_money.py::test_montos_enteros` + `unit/test_arquitectura.py::test_sin_decimal_en_dinero` |
| RF-8 | `domain/cobro.py::asignar_pagos`, `payments.Pago.medio` | `unit/domain/test_cobro.py::test_varios_pagos_por_venta` + `integration/payments/test_cobro_mixto.py` |
| RF-9 | `domain/cobro.py` (saldo pendiente) | `unit/domain/test_cobro.py::test_pago_parcial_deja_venta_abierta` |
| RF-10 | `domain/cobro.py` (`ExcesoNoEfectivo`) | `unit/domain/test_cobro.py::test_no_efectivo_mayor_al_total_rechaza` |
| RF-11 | `domain/vuelto.py::calcular_vuelto` + `shared/money.py` | `unit/domain/test_vuelto.py::test_vuelto_redondea_y_registra_ajuste` |
| RF-12 | `payments.Pago` (constraint `electronico_exige_referencia`) | `integration/payments/test_cobro.py::test_electronico_exige_referencia_y_queda_pendiente` |
| RF-13 | `domain/disponible.py`, `payments/selectors.py::efectivo_disponible` | `unit/domain/test_arqueo.py::test_solo_efectivo_suma_al_disponible` |
| RF-14 | `payments/services/propina.py`, `payments.Propina` | `integration/payments/test_propina.py::test_propina_no_integra_el_total_y_atribuye_mozo` |
| RF-15 | `shared/money.py::cuadrar_lineas`, `domain/venta.py` | `unit/shared/test_money.py::test_lineas_suman_el_total_tras_redondeo` |
| RF-16 | `sync/services/idempotencia.py` | `integration/sync/test_idempotencia.py::test_replay_no_duplica_venta` |
| RF-17 | `payments/views/cobro.py`, `payments/forms.py::EmailComprobanteForm` | `integration/notifications/test_comprobante.py::test_se_ofrece_capturar_email_al_completar` |
| RF-18 | `notifications/services/comprobante.py`, `providers/ses.py`, `tasks.py` | `integration/notifications/test_comprobante.py::test_envia_comprobante_a_la_direccion_capturada` |
| RF-19 | `payments/services/cobro.py` (rama sin email) | `test_comprobante.py::test_sin_email_el_cobro_se_completa_sin_envio` + `::test_email_invalido_no_bloquea_el_cobro` |
| RF-20 | `notifications/tasks.py` (backoff) + `reintentar_pendientes` | `integration/notifications/test_reintentos.py::test_reintento_tras_fallo_transitorio` |
| RF-21 | `payments/messages.py`, `_factura_no_disponible.html` | `integration/payments/test_vistas_cobro.py::test_mensaje_factura_no_disponible` |
| RF-22 | `domain/descuentos.py::evaluar_descuento` | `unit/domain/test_descuentos.py::test_tope_exacto_no_pide_pin` |
| RF-23 | `orders/services/descuento.py` + `accounts/services/autorizacion.py` | `integration/orders/test_descuento.py::test_sobre_el_tope_exige_pin_de_supervisor` |
| RF-24 | `domain/descuentos.py` (rama `autorizacion is not None`) | `unit/domain/test_descuentos.py::test_autorizado_no_tiene_tope_adicional` |
| RF-25 | `orders/services/anulacion_item.py` | `integration/orders/test_anulacion_item.py::test_anula_item_sin_autorizacion_y_registra_evento` |
| RF-26 | `payments/services/anulacion_venta.py` + `domain/enums.py::MotivoAnulacion` | `integration/payments/test_anulacion.py::test_exige_pin_y_motivo_de_lista_cerrada` |
| RF-27 | `orders.Venta` (tipo `ANULACION`, `venta_original`, constraint) | `test_anulacion.py::test_crea_evento_sin_modificar_la_original` + `::test_doble_anulacion_rechazada` |
| RF-28 | `audit/services/registro.py` | `integration/audit/test_registro.py::test_evento_con_actor_autorizador_motivo_y_tiempo` |
| RF-29 | `accounts/services/autorizacion.py` + `EventoAuditoria.autoautorizado` | `integration/audit/test_registro.py::test_actor_igual_autorizador_marca_autoautorizado` |
| RF-30 | `cash/services/arqueo.py::iniciar_cierre`, `conteo_ciego.html` | `integration/cash/test_conteo_ciego.py::test_pantalla_no_expone_el_esperado` |
| RF-31 | `cash/services/arqueo.py::registrar_conteo` | `integration/cash/test_arqueo.py::test_calcula_diferencia_y_exige_pin` |
| RF-32 | `cash/services/resumen.py` | `integration/cash/test_resumen.py::test_resumen_incluye_los_seis_conceptos` |
| RF-33 | `cash/tasks.py::alertar_sesiones_prolongadas`, `domain/sesion.py` | `unit/domain/test_sesion.py` + `integration/cash/test_alerta_sesion.py::test_alerta_a_las_8_horas` |
| RF-34 | `sync/services/nivel.py`, `context_processors.py`, `_nivel_operacion.html` | `integration/cash/test_nivel_visible.py::test_nivel_presente_en_toda_pantalla_de_caja` |
| RF-35 | `payments/services/cobro.py` (efectivo independiente del nivel) | `integration/payments/test_offline.py::test_efectivo_funciona_sin_internet` |
| RF-36 | `payments/services/cobro.py` (`DECLARADO_OFFLINE`) | `test_offline.py::test_electronico_declarado_queda_pendiente_de_conciliacion` |
| RF-37 | `sync/services/cola.py::drenar` | `integration/sync/test_cola.py::test_drena_en_orden_sin_duplicar` + `::test_orden_ignora_reloj_del_dispositivo` |
| RF-38 | `occurred_at` / `recorded_at` en `Venta` y `Pago` | `integration/orders/test_venta.py::test_registra_ambas_marcas_de_tiempo` |
| RF-39 | `inventory/services/stock.py` (puerto no bloqueante) + evento de auditoría | `integration/payments/test_stock_no_bloquea.py::test_venta_se_registra_aunque_el_stock_falle` |

**39/39 con módulo y test.** Ningún RF sin cobertura.

---

## 8. Qué queda explícitamente fuera de este plan

- Facturación electrónica SIFEN (spec dedicada). RF-21 solo informa al cajero.
- Integración con la API de Bancard (D8).
- `catalog`, `inventory` completo, `purchasing`, `banking`, `billing`.
- Niveles N3 y N4 completos (la spec cubre N0, N1 y N2).
- Despacho de correo desde la nube (candidato C del `stack.md`, pospuesto).

## 9. Deuda que este plan genera

- `docs/ARCHITECTURE.md` §3 debe listar `notifications/` (S3).
- `docs/PRIVACY.md` debe incorporar `Venta.email_cliente` y
  `EnvioComprobante.destinatario` antes de dar la spec por terminada.
- `docs/DEPLOYMENT.md`: dominio verificado, SPF/DKIM/DMARC y trámite de acceso de
  producción de SES.
- El puerto de `inventory` es un no-op hasta spec 003 (S2).

---

**Pendiente de aprobación explícita de Rolando.** Confirmar en particular S1, S2 y S3.
Aprobado esto, habilita `/sdd-tasks`.
