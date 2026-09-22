# Tareas — Spec 001: Caja y cobros

**Estado:** aprobado (Rolando, 2026-09-22). Las 3 `[NECESITA ACLARACIÓN]` (helpers de
`shared/` sin test propio, `accounts/admin.py` sin RF, rutas de test fuera de la lista
§6 del plan) se aceptan tal como quedaron resueltas — no bloquean la construcción.
Habilita el bucle de construcción, tarea por tarea.
**Fecha:** 2026-09-22
**Total:** 84 tareas, T1–T84.
**Entradas:** `docs/constitution.md`, `specs/001-caja-y-cobros/spec.md` (aprobada, RF-1..RF-39),
`specs/001-caja-y-cobros/plan.md` (aprobado, S1/S2/S3 confirmados), `AGENTS.md` §4.

> **Nota de revisión (2026-09-22, posterior a la aprobación).** Al arrancar el bucle de
> construcción se descubrió un bloqueo de entorno: el proyecto no tenía esqueleto Django
> (`manage.py`, `src/config/settings/`, `src/__init__.py`) y `pyproject.toml` fija
> `DJANGO_SETTINGS_MODULE = "src.config.settings.test"` para pytest-django, así que
> **cualquier** test —incluso uno de dominio puro sin ORM— rompía en la fase de colección
> con `ModuleNotFoundError: No module named 'src'`. Rolando aprobó insertar una tarea nueva
> de bootstrap como **T1** y correr toda la numeración anterior en uno (el T1 original pasó
> a T2, …, el T83 original a T84). Ninguna tarea cambió de sustancia: solo cambió su número
> y las referencias cruzadas entre tareas. El total pasa de 83 a 84.

---

## Cómo se leen estas tareas

- **Una tarea = un commit = un RF (o un grupo chico de RF hermanos) con su test.**
- Cada tarea corre el bucle de `AGENTS.md` §4: LOAD → **RED** (primero el test que falla)
  → GREEN (el mínimo para pasarlo) → GATE (`make verify`) → REVIEW → CHECKPOINT → STOP.
- El campo **Hecho cuando** es la condición *adicional* y específica de la tarea. `make verify`
  en verde (G0..G5) se da por descontado en todas: constitución §6.
- **Archivos** declara exactamente lo que la tarea abre. Están tomados de la lista de archivos
  declarados del plan (§6, y §1/§5/§7 donde §6 no los repite — ver "Aclaraciones pendientes").
  Si una tarea necesita abrir un archivo que no está en su lista, no se improvisa: se pide
  corrección del plan.
- **Modelo + su migración `0001_initial` van juntos en la misma tarea**, y separados de las
  tareas de servicio que los usan. Razón: G4 (`make migrations-check`) bloquea por migración
  faltante, y ninguna tarea cierra con una compuerta en rojo (constitución §6). El plan declara
  una sola migración por app, salvo `audit/migrations/0002_revocar_permisos.py`, que sí tiene
  tarea propia (T27).
- El orden es de dependencia real: esqueleto ejecutable → primitivas sin dependencias →
  dominio puro → modelos con migración → servicios → vistas y plantillas → E2E y documentación.

---

## Área A — Cimientos (sin dependencias)

- [x] **T1 — Esqueleto ejecutable del proyecto Django**
  - **RF:** transversal (plan §1.12) — infraestructura, no comportamiento de negocio
  - **Archivos:** `manage.py`, `src/__init__.py`, `src/config/__init__.py`,
    `src/config/settings/__init__.py`, `src/config/settings/base.py`,
    `src/config/settings/test.py`, `src/config/urls.py`, `src/config/wsgi.py`,
    `src/config/asgi.py`, `src/shared/__init__.py`, `src/domain/__init__.py`,
    `src/accounts/__init__.py`, `src/audit/__init__.py`, `src/cash/__init__.py`,
    `src/sync/__init__.py`, `src/orders/__init__.py`, `src/notifications/__init__.py`,
    `src/payments/__init__.py`, `src/inventory/__init__.py`
  - **Hecho cuando:** `uv run python manage.py check` termina sin errores y
    `uv run pytest --collect-only` recolecta `tests/unit/shared/test_money.py` sin romper con
    `ModuleNotFoundError: No module named 'src'`. En concreto: `manage.py` es el estándar de
    `django-admin startproject` apuntando a `src.config.settings`; `base.py` declara
    `INSTALLED_APPS` con las apps de `django.contrib` necesarias (`admin`, `auth`,
    `contenttypes`, `sessions`, `messages`, `staticfiles`) más las ocho apps propias de esta
    spec (`accounts`, `audit`, `cash`, `sync`, `orders`, `notifications`, `payments`,
    `inventory`) como **paquetes vacíos**: solo `__init__.py`, sin modelos, sin servicios y
    sin `apps.py` — esos archivos son de T19, T24, T28, T36, T43, T51, T57 y T64 y esta tarea
    no se adelanta a crearlos. `DATABASES` apunta a PostgreSQL por variables de entorno
    coherentes con `docker-compose.yml` (sin credenciales inventadas ni hardcodeadas) y
    `SECRET_KEY` sale del entorno; ambas se leen con `pydantic-settings` (AGENTS.md §6) y
    `DEBUG=True` no queda en el archivo commiteado. `test.py` importa de `base.py` y ajusta
    solo lo mínimo para que pytest-django arranque: el reloj fijo, el proveedor de correo en
    memoria y Celery `task_always_eager=False` del plan §1.12 llegan en T20, y
    `PROVEEDOR_CORREO` / `REMITENTE_COMPROBANTE` en T56; esta tarea no los escribe. `urls.py`
    queda con `urlpatterns` vacío (o solo el admin): las rutas de caja las agrega T35.
    `src/config/celery.py` **no** se crea acá: es de T32.
    **Nota de alcance:** `catalog/`, `purchasing/`, `banking/` y `billing/` de
    `ARCHITECTURE.md` §3 no se registran todavía en `INSTALLED_APPS` — ninguna tarea de esta
    spec las crea y `billing` está declarada fuera del alcance inicial. Entran cuando su
    propia spec las traiga.
    **Nota de inserción:** esta tarea no estaba en el documento aprobado; se agregó el
    2026-09-22 al arrancar la construcción (ver la nota de revisión del encabezado).

- [x] **T2 — Redondeo comercial en guaraníes enteros**
  - **RF:** RF-7, RF-11
  - **Archivos:** `src/shared/money.py`, `tests/unit/shared/test_money.py`
  - **Hecho cuando:** `pytest tests/unit/shared/test_money.py` pasa con
    `test_montos_enteros` y los casos de `redondear_gs` del plan §3.1: `multiplo <= 1`
    devuelve el monto tal cual, `13_300` con múltiplo `500` → `13_500`, `13_200` → `13_000`,
    `13_250` → `13_500` (mitad hacia arriba), y monto negativo. Aserciones exactas, `approx`
    prohibido (plan §5.3).

- [ ] **T3 — Cuadre de líneas contra el total redondeado**
  - **RF:** RF-15
  - **Archivos:** `src/shared/money.py`, `tests/unit/shared/test_money.py`
  - **Hecho cuando:** `pytest tests/unit/shared/test_money.py::test_lineas_suman_el_total_tras_redondeo`
    pasa: `sum(cuadrar_lineas(total, lineas)) == total` para lista vacía con total 0, una línea,
    y N líneas con diferencia positiva y negativa; el ajuste cae en la última línea (ADR 0002)
    y nunca deja un total de línea negativo.

- [ ] **T4 — Reloj inyectable**
  - **RF:** RF-1, RF-33, RF-38
  - **Archivos:** `src/shared/clock.py`, `tests/unit/shared/test_clock.py`
  - **Hecho cuando:** `pytest tests/unit/shared/test_clock.py` pasa: `RelojFijo(instante).now()`
    devuelve siempre el mismo instante consciente de zona horaria, `RelojSistema` satisface el
    `Protocol` `Clock` según `mypy --strict`, y un `RelojAvanzable` puede correr el tiempo sin
    tocar estado global.

- [x] **T5 — Resultado y jerarquía de errores de negocio**
  - **RF:** transversal (plan §1.2)
  - **Archivos:** `src/shared/result.py`, `src/shared/errors.py`, `tests/unit/shared/test_result.py`,
    `tests/unit/shared/test_errors.py`
  - **Hecho cuando:** `make lint` y `make types` en verde con mypy estricto sobre `src/shared`:
    `Resultado[T]` es genérico y `ErrorDeNegocio` expone `codigo` y `mensaje`.
    **Resuelto 2026-09-22** (ver "Aclaraciones pendientes" #1): sí se agregaron
    `tests/unit/shared/test_result.py` y `tests/unit/shared/test_errors.py` como humo mínimo;
    la verificación de comportamiento real sigue llegando con los servicios que los devuelven
    (T20 en adelante).

- [ ] **T6 — Generación de identificadores y claves de idempotencia**
  - **RF:** RF-16
  - **Archivos:** `src/shared/ids.py`
  - **Hecho cuando:** `make lint` y `make types` en verde; `UuidSecuencial` produce UUID
    determinísticos y `nueva_clave_idempotencia()` cabe en `CharField(max_length=64)`.
    `[NECESITA ACLARACIÓN]` — sin módulo de test declarado (#1); RF-16 queda cubierto de
    verdad en T37 y T60.

- [ ] **T7 — Catálogo de mensajes en español de Paraguay**
  - **RF:** RF-2, RF-5, RF-9, RF-10, RF-21 (solo las cadenas; la lógica está en sus tareas)
  - **Archivos:** `src/shared/mensajes.py`
  - **Hecho cuando:** `make lint` y `make types` en verde y existe una constante por cada uno
    de los cinco mensajes (sesión ya abierta, caja cerrada, saldo pendiente, exceso no-efectivo,
    factura formal no disponible). Cada cadena se asierta literalmente en la tarea del RF que
    la usa (T29, T58, T59, T11, T69).
    `[NECESITA ACLARACIÓN]` — sin módulo de test declarado (#1).

- [ ] **T8 — Enumeraciones y errores del dominio**
  - **RF:** RF-8, RF-26, RF-34
  - **Archivos:** `src/domain/enums.py`, `src/domain/errores.py`
  - **Hecho cuando:** `make types` en verde con mypy estricto sobre `src/domain`:
    `MedioPago` tiene los cinco medios de RF-8, `MotivoAnulacion` exactamente los tres motivos
    de la lista cerrada de RF-26, `NivelOperacion` N0..N4, y existen `SaldoInsuficiente`,
    `ExcesoNoEfectivo`, `ReferenciaRequerida`, `MotivoInvalido`, `AutorizacionRequerida`.
    Los valores se asiertan en T11, T62 y T71.

- [ ] **T9 — Test de arquitectura: sin `Decimal`, sin Django ni reloj global en el núcleo**
  - **RF:** RF-7 + invariantes del plan §5.1
  - **Archivos:** `tests/unit/test_arquitectura.py`
  - **Hecho cuando:** `pytest tests/unit/test_arquitectura.py` pasa sobre el árbol actual y
    **falla** si se introduce a propósito `from decimal import Decimal` en `src/shared/money.py`,
    `import django` en `src/domain/`, o `timezone.now()` en `src/domain`, `src/shared` o
    `*/services/*` (verificado invirtiendo el cambio antes de commitear).

---

## Área B — Dominio puro del cobro

- [ ] **T10 — Vuelto redondeado con ajuste explícito**
  - **RF:** RF-11
  - **Archivos:** `src/domain/vuelto.py`, `tests/unit/domain/test_vuelto.py`
  - **Hecho cuando:** `pytest tests/unit/domain/test_vuelto.py::test_vuelto_redondea_y_registra_ajuste`
    pasa con los tres ejemplos del plan §3.2 (`13_000`→ajuste 0, `13_300`→entregado `13_500`
    ajuste `+200`, `13_200`→entregado `13_000` ajuste `-200`) y excedente `<= 0` → `Vuelto(0,0,0)`.

- [ ] **T11 — Validaciones previas del cobro: exceso no-efectivo y referencia obligatoria**
  - **RF:** RF-10, RF-12
  - **Archivos:** `src/domain/cobro.py`, `tests/unit/domain/test_cobro.py`
  - **Hecho cuando:** `pytest tests/unit/domain/test_cobro.py::test_no_efectivo_mayor_al_total_rechaza`
    pasa: `ExcesoNoEfectivo` con el excedente exacto cuando la suma no-efectivo supera el total,
    y `ReferenciaRequerida` cuando un medio electrónico llega con referencia vacía. Ningún efecto
    de borde: la función no escribe nada.

- [ ] **T12 — Asignación de pago mixto y saldo pendiente**
  - **RF:** RF-8, RF-9
  - **Archivos:** `src/domain/cobro.py`, `tests/unit/domain/test_cobro.py`
  - **Hecho cuando:** pasan `test_varios_pagos_por_venta` y
    `test_pago_parcial_deja_venta_abierta`: lo electrónico se aplica íntegro primero, el efectivo
    cubre el saldo, y el resultado es `ABIERTA` con `saldo_pendiente > 0` o `COBRADA` con saldo 0.

- [ ] **T13 — Un solo vuelto por cobro, sobre el último pago en efectivo**
  - **RF:** RF-11 (decisión D10)
  - **Archivos:** `src/domain/cobro.py`, `tests/unit/domain/test_cobro.py`
  - **Hecho cuando:** un test de `test_cobro.py` verifica que con dos pagos en efectivo el
    vuelto y el ajuste quedan íntegros en el último aplicado, los demás en 0, y se cumple
    `recibido - monto == vuelto + ajuste` en esa fila.

- [ ] **T14 — Recálculo de totales de la venta**
  - **RF:** RF-15, RF-25
  - **Archivos:** `src/domain/venta.py`, `tests/unit/domain/test_venta.py`
  - **Hecho cuando:** `pytest tests/unit/domain/test_venta.py` pasa: `recalcular_totales`
    ignora las líneas `ANULADA`, redondea el total y ajusta la última línea vigente (ADR 0002),
    y la suma de las líneas vigentes es exactamente el total.

- [ ] **T15 — Topes de descuento y veredicto de autorización**
  - **RF:** RF-22, RF-23, RF-24
  - **Archivos:** `src/domain/descuentos.py`, `tests/unit/domain/test_descuentos.py`
  - **Hecho cuando:** pasan `test_tope_exacto_no_pide_pin`, el caso de uno menos, el de uno más
    (→ `REQUIERE_PIN`) y `test_autorizado_no_tiene_tope_adicional`
    (→ `ACEPTADO_POR_AUTORIZACION`). El tope efectivo usa `// 100`, sin `Decimal`.

- [ ] **T16 — Disponible en efectivo: solo el efectivo suma**
  - **RF:** RF-13
  - **Archivos:** `src/domain/disponible.py`, `tests/unit/domain/test_arqueo.py`
  - **Hecho cuando:** `pytest tests/unit/domain/test_arqueo.py::test_solo_efectivo_suma_al_disponible`
    pasa: QR, débito, crédito y transferencia no mueven el disponible.

- [ ] **T17 — Efectivo esperado y diferencia del arqueo**
  - **RF:** RF-31, RF-32
  - **Archivos:** `src/domain/arqueo.py`, `tests/unit/domain/test_arqueo.py`
  - **Hecho cuando:** `pytest tests/unit/domain/test_arqueo.py` pasa con la fórmula del plan
    §3.7 (`fondo + efectivo + propinas_efectivo − vueltos − sangrías`) y
    `calcular_diferencia` da positivo con sobrante, negativo con faltante y 0 exacto.

- [ ] **T18 — Sesión prolongada**
  - **RF:** RF-33
  - **Archivos:** `src/domain/sesion.py`, `tests/unit/domain/test_sesion.py`
  - **Hecho cuando:** `pytest tests/unit/domain/test_sesion.py` pasa: falso a 7 h 59 min,
    verdadero a 8 h exactas y a 8 h 01 min, con el instante pasado por parámetro.

---

## Área C — Cuentas, roles y PIN

- [ ] **T19 — Modelo `Usuario` con PIN y bloqueo por intentos**
  - **RF:** RF-4
  - **Archivos:** `src/accounts/models.py`, `src/accounts/apps.py`,
    `src/accounts/migrations/0001_initial.py`, `src/config/settings/base.py` (`AUTH_USER_MODEL`)
  - **Hecho cuando:** `make migrations-check` (G4) en verde sin migraciones pendientes y
    `python manage.py sqlmigrate accounts 0001` muestra `id` UUID como PK y las columnas
    `pin_hash`, `pin_actualizado_en`, `pin_intentos_fallidos`, `pin_bloqueado_hasta`.
    Los grupos `CAJERO`, `SUPERVISOR`, `ADMINISTRADOR`, `MOZO`, `SOPORTE` quedan como datos,
    no como constantes de código (ADR 0004).

- [ ] **T20 — Chequeo de rol en capa de servicio**
  - **RF:** RF-3, RF-6, RF-25
  - **Archivos:** `src/accounts/services/permisos.py`, `tests/conftest.py`,
    `tests/factories/accounts.py`, `tests/integration/accounts/test_permisos.py`
  - **Hecho cuando:** `pytest tests/integration/accounts/test_permisos.py` pasa contra
    PostgreSQL real: `exigir_rol(usuario, "CAJERO")` acepta al cajero y rechaza a quien no tiene
    el grupo, con error de negocio en español. `tests/conftest.py` está declarado en el Área L
    del plan y se adelanta acá porque es el piso de todo test de integración.

- [ ] **T21 — Verificación del PIN de supervisor y construcción de `Autorizacion`**
  - **RF:** RF-23, RF-31
  - **Archivos:** `src/accounts/services/autorizacion.py`, `src/accounts/selectors.py`,
    `tests/integration/accounts/test_autorizacion.py`
  - **Hecho cuando:** `pytest tests/integration/accounts/test_autorizacion.py` pasa: PIN correcto
    de un usuario con grupo `SUPERVISOR` devuelve `Autorizacion(autorizador, motivo, en)`;
    PIN incorrecto lanza `PinInvalido`; un usuario sin el grupo lanza `NoAutorizado`; y el
    selector nunca devuelve `pin_hash`. El instante viene del `clock` inyectado.

- [ ] **T22 — Bloqueo por intentos fallidos y marca de autoautorizado**
  - **RF:** RF-29
  - **Archivos:** `src/accounts/services/autorizacion.py`,
    `tests/integration/accounts/test_autorizacion.py`
  - **Hecho cuando:** pasan los tests de: 5 fallos seguidos dejan `pin_bloqueado_hasta` a
    5 minutos del `clock` y el sexto intento lanza `PinBloqueado` aun con el PIN correcto; un
    acierto resetea `pin_intentos_fallidos` a 0; y con `supervisor.id == actor.id` la
    `Autorizacion` devuelta trae `autoautorizado=True`.

- [ ] **T23 — Alta de usuarios y carga de PIN desde el admin**
  - **RF:** — (plan §1.4)
  - **Archivos:** `src/accounts/admin.py`
  - **Hecho cuando:** `make verify` en verde y `python manage.py check` sin avisos; el formulario
    del admin escribe `pin_hash` vía `make_password` y `pin_hash` no figura en `list_display`
    ni en `fields`.
    `[NECESITA ACLARACIÓN]` — el plan declara `accounts/admin.py` sin RF ni test asociado
    (ver "Aclaraciones pendientes" #2).

---

## Área D — Auditoría append-only

- [ ] **T24 — Modelo `EventoAuditoria` inmutable**
  - **RF:** RF-28
  - **Archivos:** `src/audit/models.py`, `src/audit/apps.py`,
    `src/audit/migrations/0001_initial.py`, `tests/integration/audit/test_inmutabilidad.py`
  - **Hecho cuando:** `pytest tests/integration/audit/test_inmutabilidad.py` pasa:
    `evento.delete()` lanza, `save()` sobre una fila existente lanza, el manager no expone
    `delete()`, y el `CheckConstraint` `autoautorizado_exige_autorizador` produce
    `IntegrityError` al intentar `autoautorizado=True` sin autorizador.

- [ ] **T25 — Única puerta de escritura del log**
  - **RF:** RF-28
  - **Archivos:** `src/audit/services/registro.py`, `tests/factories/audit.py`,
    `tests/integration/audit/test_registro.py`
  - **Hecho cuando:** `pytest tests/integration/audit/test_registro.py::test_evento_con_actor_autorizador_motivo_y_tiempo`
    pasa: `registrar_evento` persiste tipo, actor, autorizador, motivo, `occurred_at`,
    `recorded_at` del `clock` inyectado, y un `payload` sin ningún dato de tarjeta.

- [ ] **T26 — Marca y consulta de eventos autoautorizados**
  - **RF:** RF-29
  - **Archivos:** `src/audit/selectors.py`, `tests/integration/audit/test_registro.py`
  - **Hecho cuando:** pasa
    `test_registro.py::test_actor_igual_autorizador_marca_autoautorizado` y el selector por
    `autoautorizado=True` devuelve ese evento y no los demás.

- [ ] **T27 — `REVOKE UPDATE, DELETE` sobre la tabla del log**
  - **RF:** RF-28 (decisión D9)
  - **Archivos:** `src/audit/migrations/0002_revocar_permisos.py`,
    `tests/integration/audit/test_inmutabilidad.py`
  - **Hecho cuando:** `pytest tests/integration/audit/test_inmutabilidad.py` pasa un caso nuevo
    donde `EventoAuditoria.objects.filter(...).update(motivo="x")` y un `DELETE` crudo con el rol
    de aplicación levantan error de permisos de PostgreSQL, no solo del ORM. `make migrations-check`
    (G4) en verde.

---

## Área E — Sesión de caja y sangría

- [ ] **T28 — Modelos `Terminal`, `SesionCaja` y `Sangria` con sus constraints**
  - **RF:** RF-1, RF-2, RF-6
  - **Archivos:** `src/cash/models.py`, `src/cash/apps.py`,
    `src/cash/migrations/0001_initial.py`, `tests/integration/cash/test_sesion.py`
  - **Hecho cuando:** pasa `test_sesion.py::test_constraint_bloquea_sesion_doble`
    (`IntegrityError` al insertar una segunda sesión `ABIERTA` en la misma terminal, saltando el
    servicio) y los casos de `fondo_no_negativo`, `cierre_consistente` y `sangria_positiva`.
    `make migrations-check` en verde.

- [ ] **T29 — Apertura de sesión**
  - **RF:** RF-1, RF-2
  - **Archivos:** `src/cash/services/sesion.py`, `tests/factories/cash.py`,
    `tests/integration/cash/test_sesion.py`
  - **Hecho cuando:** pasan
    `test_apertura_registra_fondo_terminal_actor_y_tiempos` (fondo, terminal, cajero,
    `abierta_occurred_at` del dispositivo y `abierta_recorded_at` del `clock`) y
    `test_segunda_apertura_rechazada_informa_sesion_vigente`, cuyo mensaje nombra la sesión
    abierta y desde cuándo, con la cadena de `shared/mensajes.py`.

- [ ] **T30 — Sesión activa por terminal y guardia de caja abierta**
  - **RF:** RF-3, RF-4, RF-5
  - **Archivos:** `src/cash/services/sesion.py`, `tests/integration/cash/test_sesion.py`
  - **Hecho cuando:** pasan `test_operaciones_se_registran_contra_sesion_abierta`,
    `test_cajero_distinto_opera_sin_reabrir_sesion` (la sesión no cambia de `cajero_apertura`
    ni de estado) y el caso en que `exigir_sesion_abierta` sin sesión levanta `SinSesion` con
    el mensaje de "debe abrirse la caja".

- [ ] **T31 — Sangría**
  - **RF:** RF-6
  - **Archivos:** `src/cash/services/sangria.py`, `tests/integration/cash/test_sangria.py`
  - **Hecho cuando:** pasa
    `test_sangria.py::test_sangria_descuenta_y_registra_motivo_y_actor`: la sangría baja el
    disponible en efectivo, persiste motivo y actor, deja evento `SANGRIA` en el log, y corre
    bajo `atomic()` con `select_for_update()` sobre la sesión.

- [ ] **T32 — Alerta de sesión prolongada (8 horas)**
  - **RF:** RF-33
  - **Archivos:** `src/cash/tasks.py`, `src/config/celery.py`,
    `tests/integration/cash/test_alerta_sesion.py`
  - **Hecho cuando:** pasa `test_alerta_sesion.py::test_alerta_a_las_8_horas`: con el reloj
    corrido 8 h sobre `abierta_recorded_at` se emite un evento `SESION_PROLONGADA`, se marca
    `alerta_prolongada_emitida=True` y una segunda corrida no duplica la alerta; un
    `occurred_at` adelantado del dispositivo no dispara nada.

- [ ] **T33 — Pantalla de apertura de caja**
  - **RF:** RF-1
  - **Archivos:** `src/cash/forms.py` (`AperturaForm`), `src/cash/views/sesion.py`,
    `src/cash/templates/cash/apertura.html`, `tests/integration/cash/test_sesion.py`
  - **Hecho cuando:** un test con el cliente de Django postea el fondo inicial y crea la sesión;
    la vista no contiene lógica de negocio (solo parsea y delega) y el formulario es operable
    por teclado (campo con `autofocus`, envío con Enter).

- [ ] **T34 — Pantalla de sangría**
  - **RF:** RF-6
  - **Archivos:** `src/cash/forms.py` (`SangriaForm`), `src/cash/views/sesion.py`,
    `src/cash/templates/cash/sangria.html`, `tests/integration/cash/test_sangria.py`
  - **Hecho cuando:** un test postea monto y motivo, la sangría queda registrada, y un monto
    `<= 0` vuelve con error de formulario en español sin tocar la base.

- [ ] **T35 — Panel de caja y rutas**
  - **RF:** RF-3
  - **Archivos:** `src/cash/views/sesion.py`, `src/cash/templates/cash/panel.html`,
    `src/config/urls.py`, `tests/integration/cash/test_sesion.py`
  - **Hecho cuando:** un test resuelve la URL del panel, obtiene 200 con la sesión abierta y ve
    el fondo inicial y las operaciones de la sesión; sin sesión abierta redirige a la apertura.

---

## Área F — Idempotencia, cola offline y nivel de operación

- [ ] **T36 — Modelos `RegistroIdempotencia` y `OperacionEncolada`**
  - **RF:** RF-16, RF-37
  - **Archivos:** `src/sync/models.py`, `src/sync/apps.py`,
    `src/sync/migrations/0001_initial.py`, `tests/integration/sync/test_idempotencia.py`
  - **Hecho cuando:** un test verifica `IntegrityError` al insertar dos `RegistroIdempotencia`
    con la misma `clave` y dos `OperacionEncolada` con la misma `clave_idempotencia`; el índice
    `["estado", "recorded_at", "id"]` existe en el SQL de la migración.
    `make migrations-check` en verde.

- [ ] **T37 — `ejecutar_idempotente`**
  - **RF:** RF-16
  - **Archivos:** `src/sync/services/idempotencia.py`, `tests/factories/sync.py`,
    `tests/integration/sync/test_idempotencia.py`
  - **Hecho cuando:** un test corre dos veces la misma clave sobre una función que cuenta
    invocaciones: el contador queda en 1 y la segunda llamada devuelve la respuesta serializada
    de la primera.

- [ ] **T38 — Encolado y drenado de operaciones**
  - **RF:** RF-37
  - **Archivos:** `src/sync/services/cola.py`, `tests/integration/sync/test_cola.py`
  - **Hecho cuando:** pasa `test_cola.py::test_drena_en_orden_sin_duplicar`: las pendientes se
    aplican en orden `recorded_at, id`, quedan `APLICADA` con `aplicada_en` del `clock`, y un
    segundo drenado no vuelve a aplicarlas.

- [ ] **T39 — El reloj del dispositivo no gobierna el orden**
  - **RF:** RF-37 (decisión D11)
  - **Archivos:** `src/sync/services/cola.py`, `tests/integration/sync/test_cola.py`
  - **Hecho cuando:** pasa `test_cola.py::test_orden_ignora_reloj_del_dispositivo`: con una
    operación de `occurred_at` adelantado y otra atrasado, el orden de aplicación sigue
    `recorded_at`; y un error transitorio deja la operación `PENDIENTE` con `intentos+1`,
    mientras un error permanente la deja `FALLIDA` con evento en el log.

- [ ] **T40 — Tarea Celery de drenado**
  - **RF:** RF-37
  - **Archivos:** `src/sync/tasks.py`, `src/config/celery.py`,
    `tests/integration/sync/test_cola.py`
  - **Hecho cuando:** un test invoca `drenar_cola()` manualmente (con
    `task_always_eager=False`, plan §1.12) y verifica que aplica las pendientes y que el
    beat schedule declara la tarea.

- [ ] **T41 — Nivel de operación N0..N2 a partir de sondas**
  - **RF:** RF-34, RF-35, RF-36
  - **Archivos:** `src/sync/services/nivel.py`, `tests/unit/sync/test_nivel.py`
  - **Hecho cuando:** `pytest tests/unit/sync/test_nivel.py` pasa con `SondasFijas`:
    todo arriba → N0; sin internet → N1; sin LAN → N2; sin edge box → N3. Sin llamadas de red
    en el test.

- [ ] **T42 — Nivel visible de forma permanente en la pantalla de caja**
  - **RF:** RF-34
  - **Archivos:** `src/sync/context_processors.py`,
    `src/cash/templates/cash/_nivel_operacion.html`, `src/config/settings/base.py`
    (registro del context processor), `tests/integration/cash/test_nivel_visible.py`
  - **Hecho cuando:** pasa `test_nivel_visible.py::test_nivel_presente_en_toda_pantalla_de_caja`:
    el indicador aparece en apertura, panel, venta abierta, cobro y conteo; el valor se cachea
    y el render no dispara una sonda por request.
    `[NECESITA ACLARACIÓN]` — `tests/integration/cash/test_nivel_visible.py` aparece en §7 del
    plan pero no en la lista de archivos de §6 Área F (ver "Aclaraciones pendientes" #3).

---

## Área G — Venta, líneas, numeración, descuentos y anulación de ítem

- [ ] **T43 — Modelos `Venta`, `LineaVenta` y `SecuenciaTerminal`**
  - **RF:** RF-15, RF-27, RF-38
  - **Archivos:** `src/orders/models.py`, `src/orders/apps.py`,
    `src/orders/migrations/0001_initial.py`, `tests/integration/orders/test_venta.py`
  - **Hecho cuando:** tests de constraint en verde: `numero_unico_por_terminal`,
    `total_no_negativo`, `anulacion_referencia_original` (tipo `ANULACION` sin
    `venta_original` → `IntegrityError`), `anulacion_con_motivo`, `orden_unico_por_venta` y
    `cantidad_positiva`. `Venta.delete()` y `LineaVenta.delete()` lanzan.
    `make migrations-check` en verde.

- [ ] **T44 — Numeración por terminal con candado**
  - **RF:** RF-38
  - **Archivos:** `src/orders/services/numeracion.py`, `tests/factories/orders.py`,
    `tests/integration/orders/test_numeracion.py`
  - **Hecho cuando:** `pytest tests/integration/orders/test_numeracion.py` pasa: el formato es
    `establecimiento-punto-secuencia` (`001-001-0000431`) y dos llamadas concurrentes bajo
    `select_for_update()` no entregan el mismo número.

- [ ] **T45 — Creación de venta con ambas marcas de tiempo**
  - **RF:** RF-38
  - **Archivos:** `src/orders/services/venta.py`, `tests/integration/orders/test_venta.py`
  - **Hecho cuando:** pasa `test_venta.py::test_registra_ambas_marcas_de_tiempo`:
    `occurred_at` es el del dispositivo que llega por parámetro y `recorded_at` el del `clock`
    del servidor, y quedan distintos cuando el reloj del dispositivo está corrido.

- [ ] **T46 — Líneas de venta y recálculo persistido**
  - **RF:** RF-15
  - **Archivos:** `src/orders/services/venta.py`, `tests/integration/orders/test_venta.py`
  - **Hecho cuando:** un test agrega tres líneas con snapshot (`producto_id`, `descripcion`,
    `precio_unitario_gs`) y verifica que la suma de `total_gs` de las líneas vigentes es igual a
    `Venta.total_gs` después del redondeo.

- [ ] **T47 — Aplicación de descuento con y sin autorización**
  - **RF:** RF-22, RF-23, RF-24
  - **Archivos:** `src/orders/services/descuento.py`,
    `tests/integration/orders/test_descuento.py`
  - **Hecho cuando:** pasa
    `test_descuento.py::test_sobre_el_tope_exige_pin_de_supervisor`: en el tope se aplica sin
    autorización; sobre el tope sin `Autorizacion` levanta `AutorizacionRequerida` y no persiste
    nada; con `Autorizacion` válida se aplica y deja evento `DESCUENTO_AUTORIZADO`.

- [ ] **T48 — Anulación de ítem en venta abierta**
  - **RF:** RF-25
  - **Archivos:** `src/orders/services/anulacion_item.py`,
    `tests/integration/orders/test_anulacion_item.py`
  - **Hecho cuando:** pasa
    `test_anulacion_item.py::test_anula_item_sin_autorizacion_y_registra_evento`: la fila pasa a
    `ANULADA` con `anulada_por` y `anulada_en` (no se borra), se recalculan los totales, hay
    evento `ANULACION_ITEM`, y sobre una venta `COBRADA` la operación se rechaza.

- [ ] **T49 — Pantalla de la venta abierta con saldo pendiente**
  - **RF:** RF-9
  - **Archivos:** `src/orders/views/venta.py`,
    `src/orders/templates/orders/venta_abierta.html`,
    `src/orders/templates/orders/_lineas.html`, `tests/integration/orders/test_venta.py`
  - **Hecho cuando:** un test con el cliente de Django ve las líneas vigentes, las anuladas
    marcadas como tales y el saldo pendiente con el mensaje de `shared/mensajes.py`.

- [ ] **T50 — Diálogo de PIN para descuento sobre el tope**
  - **RF:** RF-23
  - **Archivos:** `src/orders/views/venta.py`,
    `src/orders/templates/orders/_descuento_pin.html`,
    `tests/integration/orders/test_descuento.py`
  - **Hecho cuando:** un test verifica que un descuento sobre el tope devuelve la pantalla con el
    pedido de PIN, que el PIN nunca viaja en la URL ni queda en el log, y que la vista no puede
    construir una `Autorizacion` por su cuenta (solo la recibe del servicio de `accounts`).

---

## Área J (primera parte) — Comprobante por correo

> Se adelanta al Área H porque `payments/services/cobro.py` invoca `encolar_comprobante`
> (plan §3.4). `notifications` no conoce `cash` ni `payments`: recibe un DTO y una dirección.

- [ ] **T51 — Modelo `EnvioComprobante`**
  - **RF:** RF-18, RF-20
  - **Archivos:** `src/notifications/models.py`, `src/notifications/apps.py`,
    `src/notifications/migrations/0001_initial.py`,
    `tests/integration/notifications/test_comprobante.py`
  - **Hecho cuando:** un test verifica `IntegrityError` con `clave_idempotencia` repetida, que
    el índice `["estado", "encolado_en"]` existe, y que `cuerpo_datos` no admite datos de tarjeta
    más allá de `ultimos_cuatro`. `make migrations-check` en verde.

- [ ] **T52 — Puerto de correo y adaptador en memoria**
  - **RF:** RF-18
  - **Archivos:** `src/notifications/providers/base.py`,
    `src/notifications/providers/memoria.py`,
    `tests/integration/notifications/test_comprobante.py`
  - **Hecho cuando:** un test verifica que `ProveedorEnMemoria` acumula los `MensajeCorreo`
    enviados y que `forzar_fallo(reintentable=True/False)` devuelve el `ResultadoEnvio`
    correspondiente. `mypy --strict` confirma que ningún tipo de AWS cruza `base.py`.

- [ ] **T53 — Encolado del comprobante y email ausente o inválido**
  - **RF:** RF-18, RF-19
  - **Archivos:** `src/notifications/services/comprobante.py`,
    `tests/factories/notifications.py`,
    `tests/integration/notifications/test_comprobante.py`
  - **Hecho cuando:** pasan `test_sin_email_el_cobro_se_completa_sin_envio` y
    `test_email_invalido_no_bloquea_el_cobro`: con email vacío o de formato inválido
    `encolar_comprobante` devuelve `None` sin crear fila; con email válido crea el
    `EnvioComprobante` en `PENDIENTE` con `clave_idempotencia = cmp-<venta_id>`.

- [ ] **T54 — Despacho del comprobante y cuerpo del correo**
  - **RF:** RF-18
  - **Archivos:** `src/notifications/services/comprobante.py`,
    `src/notifications/templates/notifications/comprobante.html`,
    `src/notifications/templates/notifications/comprobante.txt`,
    `tests/integration/notifications/test_comprobante.py`
  - **Hecho cuando:** pasa
    `test_comprobante.py::test_envia_comprobante_a_la_direccion_capturada`: el envío queda
    `ENVIADO` con `mensaje_id` y `enviado_en`; el cuerpo trae número, líneas y total, la leyenda
    explícita de "sin valor fiscal" (RF-21), y ningún dato de tarjeta; un envío ya `ENVIADO` es
    idempotente.

- [ ] **T55 — Reintentos con backoff y red de seguridad**
  - **RF:** RF-20
  - **Archivos:** `src/notifications/tasks.py`, `src/config/celery.py`,
    `tests/integration/notifications/test_reintentos.py`
  - **Hecho cuando:** pasa
    `test_reintentos.py::test_reintento_tras_fallo_transitorio`: un fallo reintentable deja el
    envío en `PENDIENTE` con `intentos+1` y reprograma con la escalera 1m/5m/15m/1h/6h hasta
    8 intentos; un fallo duro lo deja `FALLIDO` con evento `FALLA_ENVIO_COMPROBANTE`; y
    `reintentar_pendientes()` recoge los `PENDIENTE` viejos.

- [ ] **T56 — Adaptadores SES y consola, y configuración del proveedor**
  - **RF:** RF-18
  - **Archivos:** `src/notifications/providers/ses.py`,
    `src/notifications/providers/consola.py`, `src/config/settings/base.py`
    (`PROVEEDOR_CORREO`, `REMITENTE_COMPROBANTE`),
    `tests/integration/notifications/test_comprobante.py`
  - **Hecho cuando:** un test con `override_settings(PROVEEDOR_CORREO="CONSOLA")` verifica que
    el despacho usa el adaptador de consola y persiste `proveedor="CONSOLA"`; el adaptador SES
    traduce sus errores a `ResultadoEnvio(reintentable=…)` sin filtrar excepciones de boto3
    hacia arriba. **Tarea de infraestructura previa (plan §6):** dominio verificado en SES y
    acceso de producción solicitado.

---

## Área H — Cobro, pagos, propina y puerto de stock

- [ ] **T57 — Modelos `Pago` y `Propina` con sus constraints**
  - **RF:** RF-8, RF-12, RF-13
  - **Archivos:** `src/payments/models.py`, `src/payments/apps.py`,
    `src/payments/migrations/0001_initial.py`,
    `tests/integration/payments/test_cobro.py`
  - **Hecho cuando:** tests de constraint en verde contra la base, salteando el servicio:
    `electronico_exige_referencia`, `efectivo_siempre_acreditado`,
    `sin_vuelto_en_electronico` y `pago_positivo` levantan `IntegrityError`; `Pago.delete()` y
    `Propina.delete()` lanzan. `make migrations-check` en verde.

- [ ] **T58 — Orquestador del cobro: sesión, rol y creación de pagos**
  - **RF:** RF-5, RF-8
  - **Archivos:** `src/payments/services/cobro.py`, `tests/factories/payments.py`,
    `tests/integration/payments/test_cobro.py`
  - **Hecho cuando:** pasan `test_cobro_sin_sesion_rechazado` (mensaje "debe abrirse la caja",
    nada persistido) y `test_pago_exacto`: con sesión abierta se crean los `Pago` bajo
    `atomic()` con `select_for_update()` sobre `SesionCaja`, y el rol se exige en el servicio,
    no en la vista.

- [ ] **T59 — Estado de la venta, vuelto entregado y ajuste de redondeo persistidos**
  - **RF:** RF-9, RF-11
  - **Archivos:** `src/payments/services/cobro.py`,
    `tests/integration/payments/test_cobro.py`
  - **Hecho cuando:** pasan `test_pago_con_vuelto` (con `REDONDEO_VUELTO_GS=500` el `Pago`
    guarda `recibido_gs`, `vuelto_gs` y `ajuste_redondeo_gs`, y se cumple
    `recibido - monto == vuelto + ajuste`) y `test_pago_parcial_deja_venta_abierta`
    (venta `ABIERTA` con el saldo informado).

- [ ] **T60 — Cobro idempotente**
  - **RF:** RF-16
  - **Archivos:** `src/payments/services/cobro.py`,
    `tests/integration/sync/test_idempotencia.py`
  - **Hecho cuando:** pasa `test_idempotencia.py::test_replay_no_duplica_venta`: la misma clave
    recibida dos veces deja una sola `Venta` y un solo `Pago`, y la segunda llamada devuelve el
    `ResultadoCobro` de la primera.

- [ ] **T61 — Cobro mixto de punta a punta**
  - **RF:** RF-8, RF-10
  - **Archivos:** `src/payments/services/cobro.py`,
    `tests/integration/payments/test_cobro_mixto.py`
  - **Hecho cuando:** pasan `test_mixto_exacto` (QR + efectivo que suman el total → `COBRADA`,
    un `Pago` por medio), `test_mixto_incompleto` (deja la venta `ABIERTA`, no rechaza) y el caso
    de no-efectivo mayor al total, que rechaza informando el exceso sin persistir nada.
    Se agrega `test_select_for_update_serializa_dos_cobros` (dos terminales sobre la misma venta).

- [ ] **T62 — Operación sin internet: efectivo completo y electrónico declarado**
  - **RF:** RF-35, RF-36
  - **Archivos:** `src/payments/services/cobro.py`,
    `tests/integration/payments/test_offline.py`
  - **Hecho cuando:** pasan `test_efectivo_funciona_sin_internet` (con
    `SondasFijas(internet=False)` el cobro en efectivo se completa igual y la venta guarda
    `nivel_operacion="N1"`) y
    `test_electronico_declarado_queda_pendiente_de_conciliacion`
    (`Pago.estado == "DECLARADO_OFFLINE"` con su referencia).

- [ ] **T63 — Propina fuera del total, atribuida al mozo**
  - **RF:** RF-14
  - **Archivos:** `src/payments/services/propina.py`,
    `tests/integration/payments/test_propina.py`
  - **Hecho cuando:** pasa
    `test_propina.py::test_propina_no_integra_el_total_y_atribuye_mozo`: `Venta.total_gs` no
    cambia, la `Propina` guarda `mozo_id` y medio, y si el medio es efectivo entra al efectivo
    esperado del cierre.

- [ ] **T64 — Puerto de stock no bloqueante**
  - **RF:** RF-39
  - **Archivos:** `src/inventory/services/stock.py`, `src/inventory/apps.py`,
    `src/payments/services/cobro.py`,
    `tests/integration/payments/test_stock_no_bloquea.py`
  - **Hecho cuando:** pasa
    `test_stock_no_bloquea.py::test_venta_se_registra_aunque_el_stock_falle`: con un
    `StockQueExplota` inyectado, la venta queda `COBRADA` y persistida, y se registra un evento
    `ALERTA_STOCK_NEGATIVO` con el error en el payload. La llamada ocurre fuera del `atomic()`.

- [ ] **T65 — Selectores de pagos para el cierre**
  - **RF:** RF-13, RF-32
  - **Archivos:** `src/payments/selectors.py`,
    `tests/integration/payments/test_cobro.py`
  - **Hecho cuando:** un test verifica que `total_efectivo`, `total_vuelto`,
    `total_ajuste_redondeo`, `total_propina_efectivo` y `pagos_por_medio` devuelven los montos
    de la sesión, y que solo el efectivo suma al disponible.

- [ ] **T66 — Captura del correo al completar el cobro**
  - **RF:** RF-17, RF-19
  - **Archivos:** `src/payments/services/cobro.py`, `src/payments/forms.py`
    (`EmailComprobanteForm`),
    `src/payments/templates/payments/_email_comprobante.html`,
    `tests/integration/notifications/test_comprobante.py`
  - **Hecho cuando:** pasa
    `test_comprobante.py::test_se_ofrece_capturar_email_al_completar`: al completar el total se
    ofrece el campo de correo; con correo capturado la venta guarda `email_cliente` y se encola
    el envío con `transaction.on_commit`; sin correo el cobro se completa igual, sin envío y sin
    error.

- [ ] **T67 — Pantalla de cobro operable por teclado**
  - **RF:** RF-8, RF-12
  - **Archivos:** `src/payments/forms.py` (`PagoForm`, `CobroForm`),
    `src/payments/views/cobro.py`, `src/payments/templates/payments/cobro.html`,
    `tests/integration/payments/test_cobro.py`
  - **Hecho cuando:** un test postea un cobro de varios pagos desde el cliente de Django y la
    venta queda `COBRADA`; un medio electrónico sin referencia vuelve con error de formulario en
    español; la pantalla se opera sin mouse (orden de tabulación explícito y `autofocus`).

- [ ] **T68 — Detalle de pagos y vuelto en pantalla**
  - **RF:** RF-11
  - **Archivos:** `src/payments/views/cobro.py`,
    `src/payments/templates/payments/_pago_linea.html`,
    `src/payments/templates/payments/_vuelto.html`,
    `tests/integration/payments/test_cobro.py`
  - **Hecho cuando:** un test verifica que la pantalla muestra el vuelto entregado ya redondeado
    y, cuando hay ajuste, el ajuste por separado; nunca se muestra el vuelto bruto como si fuera
    el entregado.

- [ ] **T69 — Mensaje de factura formal no disponible**
  - **RF:** RF-21
  - **Archivos:** `src/payments/messages.py`,
    `src/payments/templates/payments/_factura_no_disponible.html`,
    `src/payments/views/cobro.py`,
    `tests/integration/payments/test_vistas_cobro.py`
  - **Hecho cuando:** pasa
    `test_vistas_cobro.py::test_mensaje_factura_no_disponible`: al pedir factura formal la
    pantalla muestra el texto exacto de `payments/messages.py` en español de Paraguay y ofrece
    el comprobante interno como alternativa; el cobro no se interrumpe.
    `[NECESITA ACLARACIÓN]` — `tests/integration/payments/test_vistas_cobro.py` aparece en §5.4
    y §7 del plan pero no en la lista de archivos de §6 Área H (#3).

- [ ] **T70 — Test de arquitectura: el cobro no puede bloquearse por un tercero**
  - **RF:** RF-39 + invariantes del plan §5.1
  - **Archivos:** `tests/unit/test_arquitectura.py`
  - **Hecho cuando:** el test falla si aparece una llamada a `notifications`, `inventory` o
    `sync` dentro del bloque `atomic()` de `registrar_cobro`, y si alguna app importa modelos de
    otra app (solo se cruzan servicios y selectores, plan §1.1).

---

## Área I — Anulación de venta cobrada

- [ ] **T71 — Anulación con PIN y motivo de lista cerrada**
  - **RF:** RF-26
  - **Archivos:** `src/payments/services/anulacion_venta.py`,
    `tests/integration/payments/test_anulacion.py`
  - **Hecho cuando:** pasa
    `test_anulacion.py::test_exige_pin_y_motivo_de_lista_cerrada`: sin `Autorizacion` levanta
    `AutorizacionRequerida`; con un motivo fuera de `MotivoAnulacion` levanta `MotivoInvalido`;
    con los tres motivos válidos de RF-26 se acepta. Ninguna rama inválida persiste nada.

- [ ] **T72 — La anulación es un evento nuevo, no una edición**
  - **RF:** RF-27
  - **Archivos:** `src/payments/services/anulacion_venta.py`,
    `tests/integration/payments/test_anulacion.py`
  - **Hecho cuando:** pasan `test_crea_evento_sin_modificar_la_original` (se crea una `Venta`
    tipo `ANULACION` con `venta_original` apuntando a la cobrada, cuyos campos y `total_gs`
    quedan idénticos byte a byte) y `test_doble_anulacion_rechazada` (la segunda anulación de la
    misma venta se rechaza).

- [ ] **T73 — Auditoría de la anulación**
  - **RF:** RF-28, RF-29
  - **Archivos:** `src/payments/services/anulacion_venta.py`,
    `tests/integration/payments/test_anulacion.py`
  - **Hecho cuando:** un test verifica el evento `ANULACION_VENTA` con actor, autorizador,
    motivo, `objeto_tipo="Venta"`, `objeto_id` y payload con el total; y que cuando el cajero
    autoriza su propia anulación el evento queda con `autoautorizado=True`.

- [ ] **T74 — Pantalla de anulación con PIN de supervisor**
  - **RF:** RF-26
  - **Archivos:** `src/payments/views/anulacion.py`,
    `src/payments/templates/payments/anulacion.html`,
    `src/payments/templates/payments/_pin_supervisor.html`,
    `tests/integration/payments/test_anulacion.py`
  - **Hecho cuando:** un test postea la anulación con PIN y motivo elegido de un `select` con
    solo los tres motivos de RF-26; un PIN inválido vuelve con error y sin anulación; el PIN no
    aparece en el log ni en la URL.

---

## Área K — Arqueo ciego y cierre

- [ ] **T75 — Inicio del cierre sin exponer el esperado**
  - **RF:** RF-30
  - **Archivos:** `src/cash/services/arqueo.py`,
    `tests/integration/cash/test_conteo_ciego.py`
  - **Hecho cuando:** pasa
    `test_conteo_ciego.py::test_pantalla_no_expone_el_esperado`: `iniciar_cierre` devuelve solo
    `sesion_id` y las denominaciones; el esperado, el total de ventas y el disponible no están
    en el objeto devuelto ni se calculan en esta llamada.

- [ ] **T76 — Registro del conteo, diferencia y cierre con PIN**
  - **RF:** RF-31
  - **Archivos:** `src/cash/services/arqueo.py`, `tests/integration/cash/test_arqueo.py`
  - **Hecho cuando:** pasa `test_arqueo.py::test_calcula_diferencia_y_exige_pin` más los tres
    casos de sobrante, faltante y exacto: el conteo se persiste **antes** de calcular el
    esperado (verificable porque `efectivo_esperado_gs` sigue en `None` hasta después del
    `save()` del conteo), sin `Autorizacion` no se cierra, y el cierre deja
    `supervisor_cierre`, `cerrada_recorded_at` y evento `CIERRE_CAJA`.

- [ ] **T77 — Resumen de cierre con los seis conceptos**
  - **RF:** RF-32
  - **Archivos:** `src/cash/services/resumen.py`, `tests/integration/cash/test_resumen.py`
  - **Hecho cuando:** pasa `test_resumen.py::test_resumen_incluye_los_seis_conceptos`:
    fondo inicial, ventas por medio de pago, sangrías, efectivo esperado, efectivo contado y
    diferencia; el módulo consume `payments/selectors.py` y no importa `Pago`.

- [ ] **T78 — Pantalla de conteo ciego**
  - **RF:** RF-30
  - **Archivos:** `src/cash/forms.py` (`ConteoForm`), `src/cash/views/cierre.py`,
    `src/cash/templates/cash/conteo_ciego.html`,
    `tests/integration/cash/test_conteo_ciego.py`
  - **Hecho cuando:** un test verifica que el contexto de la vista y el HTML renderizado no
    contienen el monto esperado ni el total de ventas (búsqueda literal sobre el cuerpo de la
    respuesta), y que el conteo se envía con el teclado.

- [ ] **T79 — Pantalla de resumen de cierre**
  - **RF:** RF-32
  - **Archivos:** `src/cash/views/cierre.py`,
    `src/cash/templates/cash/resumen_cierre.html`,
    `tests/integration/cash/test_resumen.py`
  - **Hecho cuando:** un test verifica que la pantalla muestra los seis conceptos, señala el
    ajuste de redondeo por separado y marca la diferencia como sobrante o faltante en español.

---

## Área L — E2E, documentación y validación

- [ ] **T80 — E2E del flujo de caja**
  - **RF:** RF-1..RF-39 (humo)
  - **Archivos:** `tests/e2e/test_flujo_caja.py`, `tests/conftest.py`
  - **Hecho cuando:** `make e2e` pasa el escenario de "Criterios de finalización" de la spec:
    abrir caja, cobrar tres ventas (efectivo, mixta, electrónica), descuento sobre el tope con
    autorización, anulación de una venta cobrada, y cierre con conteo ciego y diferencia.

- [ ] **T81 — E2E del modo degradado**
  - **RF:** RF-34, RF-35, RF-36, RF-37
  - **Archivos:** `tests/e2e/test_flujo_degradado.py`
  - **Hecho cuando:** `make e2e` pasa el segundo escenario: con las sondas en `internet=False`
    se cobra en efectivo y se declara un pago electrónico; al restablecer la conexión la cola
    drena y el conteo de ventas no cambia (ninguna duplicada).

- [ ] **T82 — Arquitectura y privacidad al día**
  - **RF:** — (deuda declarada, plan §9)
  - **Archivos:** `docs/ARCHITECTURE.md`, `docs/PRIVACY.md`
  - **Hecho cuando:** `ARCHITECTURE.md` §3 lista `notifications/` con su razón de cambio (S3), y
    `PRIVACY.md` documenta `Venta.email_cliente` y `EnvioComprobante.destinatario` con finalidad,
    retención y base legal. La auditoría de privacidad del pipeline no reporta campo personal sin
    ficha.

- [ ] **T83 — Despliegue del correo**
  - **RF:** — (deuda declarada, plan §9)
  - **Archivos:** `docs/DEPLOYMENT.md`
  - **Hecho cuando:** el documento incluye dominio verificado, SPF/DKIM/DMARC y el estado del
    trámite de acceso de producción de SES, y `PROVEEDOR_CORREO=CONSOLA` queda documentado como
    el valor de desarrollo mientras SES esté en sandbox.

- [ ] **T84 — Mapa de validación RF → test**
  - **RF:** RF-1..RF-39
  - **Archivos:** `specs/001-caja-y-cobros/validation.md`
  - **Hecho cuando:** los 39 RF tienen al menos un test nombrado y en verde, cada ruta de test
    del documento existe en el árbol, y `make ship` (verify + G6) pasa entero.

---

## Aclaraciones pendientes

Las tres cosas que el plan no alcanza a cubrir para descomponer sin adivinar. Ninguna bloquea
el arranque: todas caen en tareas tardías o de bajo riesgo.

1. **Área A sin módulo de test para cuatro primitivas.** §6 Área A declara
   `tests/unit/shared/test_money.py`, `tests/unit/shared/test_clock.py` y
   `tests/unit/test_arquitectura.py`, pero no un módulo de test para `shared/result.py`,
   `shared/errors.py`, `shared/ids.py` ni `shared/mensajes.py`. T5, T6 y T7 cierran contra G0/G1
   y quedan verificadas de verdad recién en las tareas que las consumen. *Pregunta:* ¿se agrega
   un módulo de test para estas primitivas, o se acepta la verificación indirecta?
   **Resuelto 2026-09-22 para T5:** sí, se agregaron `tests/unit/shared/test_result.py` y
   `tests/unit/shared/test_errors.py` como humo mínimo (ver T5). La verificación de
   comportamiento real sigue llegando en T20 en adelante, como decía el texto original. T6 y
   T7 quedan sin resolver por esta nota.

2. **`src/accounts/admin.py` sin RF ni test.** §1.4 y §6 Área C lo declaran, pero ningún RF ni
   ninguna fila de §7 lo cubre. T23 cierra contra `make verify` y `manage.py check`.
   *Pregunta:* ¿alcanza, o el alta de PIN merece su propio test de integración?

3. **Tres rutas nombradas fuera de §6.** El plan dice que el bucle abre *solo* los archivos del
   Área en §6, pero estas tres aparecen únicamente en otras secciones:
   `tests/integration/payments/test_vistas_cobro.py` (§5.4, §7 — RF-21, usada en T69),
   `tests/integration/cash/test_nivel_visible.py` (§7 — RF-34, usada en T42) y
   `src/config/settings/test.py` (§1.12 — reloj fijo, proveedor en memoria; se abre en T20 junto
   con `tests/conftest.py`). *Pregunta:* ¿se incorporan a §6 en las Áreas H, F y C
   respectivamente, o van a otra parte?

**Nota de orden (no es una aclaración):** `tests/conftest.py` está declarado en el Área L del
plan, pero es el piso de todo test de integración; se adelanta a T20. No se inventa ninguna ruta:
el archivo ya está declarado.

---

## Cobertura de RF por tarea

| RF | Tareas |
|---|---|
| RF-1 | T4, T19 (modelo), T28, T29, T33 |
| RF-2 | T7, T28, T29 |
| RF-3 | T20, T30, T35 |
| RF-4 | T19, T30 |
| RF-5 | T7, T30, T58 |
| RF-6 | T20, T28, T31, T34 |
| RF-7 | T2, T9 |
| RF-8 | T8, T12, T57, T58, T61, T67 |
| RF-9 | T7, T12, T49, T59 |
| RF-10 | T7, T11, T61 |
| RF-11 | T2, T10, T13, T59, T68 |
| RF-12 | T11, T57, T67 |
| RF-13 | T16, T57, T65 |
| RF-14 | T63 |
| RF-15 | T3, T14, T43, T46 |
| RF-16 | T6, T36, T37, T60 |
| RF-17 | T66 |
| RF-18 | T51, T52, T53, T54, T56 |
| RF-19 | T53, T66 |
| RF-20 | T51, T55 |
| RF-21 | T7, T54, T69 |
| RF-22 | T15, T47 |
| RF-23 | T15, T21, T47, T50 |
| RF-24 | T15, T47 |
| RF-25 | T14, T20, T48 |
| RF-26 | T8, T71, T74 |
| RF-27 | T43, T72 |
| RF-28 | T24, T25, T27, T73 |
| RF-29 | T22, T26, T73 |
| RF-30 | T75, T78 |
| RF-31 | T17, T21, T76 |
| RF-32 | T17, T65, T77, T79 |
| RF-33 | T4, T18, T32 |
| RF-34 | T8, T41, T42 |
| RF-35 | T41, T62 |
| RF-36 | T41, T62 |
| RF-37 | T36, T38, T39, T40, T81 |
| RF-38 | T4, T43, T44, T45 |
| RF-39 | T64, T70 |

**39/39 RF con al menos una tarea y un test nombrado.**

---

**Pendiente de aprobación explícita de Rolando.** Confirmar en particular las tres aclaraciones
de arriba y el criterio de que modelo + `0001_initial` van en la misma tarea (por G4). Aprobado
esto, habilita el bucle de construcción desde T2.
