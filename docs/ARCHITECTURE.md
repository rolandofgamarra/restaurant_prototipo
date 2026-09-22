# ARCHITECTURE.md

Forma del sistema. Un agente lee esto en vez de deducir la arquitectura leyendo código.

## 1. Topología

Arquitectura híbrida con servidor local (edge) — ver `adr/0001`.

```
        LOCAL DEL RESTAURANTE                       NUBE
 ┌────────────────────────────────┐        ┌──────────────────────┐
 │  Caja 1 ─┐                     │        │  Django (réplica)    │
 │  Caja 2 ─┤                     │        │  PostgreSQL          │
 │  KDS    ─┼── LAN ── edge box   │◄─────► │  Panel admin remoto  │
 │  Mozos  ─┘        Django       │  sync  │  Analítica           │
 │  (PWA)            PostgreSQL   │        │  Backups             │
 │                   Redis        │        └──────────────────────┘
 └────────────────────────────────┘                 ▲
              │                                     │
              └── POS Bancard / QR ─────────────────┘
                  (conectividad propia)
```

El edge box es la fuente de verdad durante la operación. La nube es réplica, analítica,
respaldo y acceso remoto del administrador.

## 2. Niveles de degradación

El nivel activo se muestra **siempre** en la interfaz de caja. El cajero tiene que saber
en qué modo está operando.

| Nivel | Situación | Qué funciona | Qué se degrada |
|---|---|---|---|
| N0 | Todo en línea | Todo | — |
| N1 | Sin internet, LAN viva | Operación completa local | Tarjeta/QR pasan a "declarado"; sync encolado; facturación en contingencia |
| N2 | Sin LAN / router caído | Cada terminal sola, cola local | Comanda a cocina por impresión; sin visión entre terminales |
| N3 | Edge box caído | Caja en modo autónomo (PWA) | Solo ventas; sin stock en vivo |
| N4 | Sin energía / hardware muerto | Talonario de papel | Carga posterior como "venta diferida", con actor y motivo |

Invariante: **cobrar en efectivo es posible en los cinco niveles.**

## 3. Contextos acotados (apps Django)

Monolito modular. Una app por contexto. Las apps se comunican por servicios, nunca
importando modelos ajenos directamente.

```
src/
  shared/        money.py, ids.py, clock.py, result.py   (sin dependencias de apps)
  domain/        reglas puras, sin Django ORM            (testeable sin BD)
  accounts/      usuarios, roles, PIN de autorización
  catalog/       carta, productos, precios versionados, recetas
  orders/        mesas, mozos, pedidos, comandas (KDS)
  payments/      medios de pago, pagos mixtos, acreditación, comisiones
  cash/          sesión de caja, fondo, sangrías, arqueo ciego, cierre
  inventory/     insumos, stock, movimientos, alertas de reposición
  purchasing/    proveedores, órdenes de compra, recepción, cuentas por pagar
  banking/       conciliación bancaria, cuentas, depósitos
  audit/         log append-only, eventos, panel por rol
  sync/          cola offline, idempotencia, reconciliación
  notifications/ envío de comprobantes al cliente (email, detrás de interfaz propia
                 `providers/base.py`; ver ADR y specs/001 stack.md — proveedor
                 transaccional tipo SES, disparado por Celery, nunca síncrono)
  billing/       facturación (SIFEN vía facilitador) — FUERA DEL ALCANCE INICIAL
```

Regla de dependencias (se verifica en G1):

```
shared  <- domain <- apps <- views
```

`domain` no importa Django. `shared` no importa nada del proyecto. Una app puede llamar
al servicio de otra; no puede importar su modelo.

## 4. Decisiones transversales

- **Single-tenant**: una instancia y una base por cliente. Aislamiento total, despliegue
  simple, sin riesgo de fuga entre locales. Se revisará si el número de clientes lo exige.
- **UI**: Django templates + HTMX + Alpine.js. Renderizado en servidor, sin SPA. La caja
  necesita ser rápida y predecible, no reactiva. Un service worker cubre el modo N3.
- **Async**: Celery + Redis para sincronización, reintentos de cola y tareas programadas.
- **Terceros detrás de una interfaz propia**: Bancard y SIFEN se consumen a través de un
  puerto definido por nosotros (`payments/gateways/base.py`, `billing/providers/base.py`).
  Ningún tipo del proveedor cruza hacia el dominio. Permite cambiar de facilitador sin
  tocar la lógica de negocio.

## 5. Modelo de eventos (núcleo)

```
Venta            uuid, terminal, numero_local, estado, occurred_at, recorded_at, actor
  └─ LineaVenta  producto, cantidad, precio_unitario_gs, descuento_gs, total_gs
  └─ Pago        medio, monto_gs, referencia, estado, acreditacion_estimada, comision_gs
EventoAuditoria  uuid, tipo, actor, autorizador, motivo, payload, occurred_at, recorded_at
MovimientoStock  uuid, insumo, delta, motivo, origen_venta, tentativo, occurred_at
SesionCaja       uuid, cajero, fondo_inicial_gs, apertura, cierre, arqueo, diferencia_gs
```

Todos con PK `UUIDField`. Ninguno admite `DELETE`. Una anulación crea una `Venta` de tipo
`ANULACION` que referencia la original y un `EventoAuditoria` con el autorizador.

## 6. Dinero

Ver `adr/0002`. Resumen operativo para el agente:

- Todo monto es `BigIntegerField`, en guaraníes enteros.
- `Decimal` y `float` están prohibidos en cualquier campo o cálculo de dinero.
- Un solo punto de redondeo: `shared/money.py::redondear_gs`.
- La suma de las líneas debe igualar el total: se redondea el total y se ajusta la última línea.
- Solo el efectivo suma a "disponible en caja". Tarjeta, QR y transferencia van a
  "pendiente de acreditación" hasta que el administrador concilie.
- La propina es una línea aparte y no es ingreso de la venta.
