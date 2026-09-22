# PRIVACY.md — inventario vivo de datos sensibles

Se actualiza en cada `/sdd-audit-privacy`. Un dato sin propósito justificado es un
hallazgo, no una columna más.

Este documento es una revisión de ingeniería. **No es asesoría legal.**

## Principios

1. **Mínimo dato.** Si la spec no lo exige, no se recolecta.
2. **Mínimo privilegio.** El acceso se verifica en la capa de servicios, por rol.
3. **Trazabilidad.** Toda lectura o modificación de un dato sensible deja evento de auditoría.
4. **Nunca se almacena** ningún dato de tarjeta más allá de los últimos cuatro dígitos.

## Inventario

| Dato | Por qué | Dónde | Quién lo lee | Retención | Cómo se borra |
|---|---|---|---|---|---|
| Nombre y usuario del empleado | Atribución de acciones en auditoría | `accounts` | Supervisor, administrador | Mientras dure la relación laboral + periodo legal | Anonimización, conservando el evento |
| PIN de autorización | Autorizar acciones elevadas | `accounts` | Nadie — se almacena con hash | Hasta su rotación | Rotación |
| Últimos 4 dígitos de tarjeta | Conciliación de acreditaciones | `payments` | Administrador | [NECESITA ACLARACIÓN: periodo] | Purga programada |
| Nº de lote / transacción del POS | Conciliación bancaria | `payments` | Administrador | Igual que el anterior | Purga programada |
| Referencia de transferencia o QR | Conciliación bancaria | `payments` | Administrador | Igual que el anterior | Purga programada |
| Monto y detalle de venta | Operación y contabilidad | `orders`, `payments` | Según rol | Periodo legal fiscal | No se borra dentro del plazo |
| Diferencias de arqueo por cajero | Control interno | `cash`, `audit` | Supervisor, administrador | [NECESITA ACLARACIÓN: periodo] | Purga programada |

## Datos que NO se almacenan, en ninguna circunstancia

- Número completo de tarjeta, fecha de vencimiento, CVV, banda magnética o chip.
- Credenciales bancarias del cliente o del local.
- Datos personales del cliente final más allá de lo que exija la facturación cuando se
  integre (y solo entonces, con su propia entrada en esta tabla).

## Pendiente

- [NECESITA ACLARACIÓN] Plazos de retención legal aplicables en Paraguay para registros
  de venta y datos de pago. Se verifica contra normativa vigente, no de memoria.
