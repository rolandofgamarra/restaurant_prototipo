# ADR 0002 — Guaraníes como enteros, con un único punto de redondeo

**Estado:** aceptada
**Fecha:** 2026-09-22

## Contexto

El guaraní no tiene decimales en circulación. Los montos son grandes: una cuenta de mesa
ronda los cientos de miles y la venta mensual los cientos de millones. Sin embargo, los
decimales sí aparecen en dos cálculos inevitables: los descuentos porcentuales y el
desglose del IVA (un IVA 10% incluido es `monto / 11`).

## Decisión

1. Todo monto se almacena como `BigIntegerField`, en guaraníes enteros. `Decimal` y
   `float` quedan prohibidos en cualquier campo o cálculo de dinero. La prohibición se
   verifica en la compuerta G0 (regla de ruff y hook de pre-commit).
2. Existe **una sola** función de redondeo: `src/shared/money.py::redondear_gs`. Ningún
   otro lugar redondea.
3. Regla de cuadre: se redondea el total y se ajusta la última línea, de modo que la suma
   de las líneas iguale siempre al total. Nunca al revés.
4. El formato de presentación vive en un único filtro de template (`guaranies`):
   `Gs. 13.500`, punto como separador de miles.
5. El redondeo del vuelto es un parámetro de configuración (`REDONDEO_VUELTO_GS`), no una
   constante en el código ni una discusión con el cajero.

## Alternativa descartada

`DecimalField(max_digits=12, decimal_places=0)`. Funciona y es correcta, pero arrastra la
aritmética de `Decimal` a todo el dominio, invita a que alguien agregue
`decimal_places=2` "por las dudas", y no aporta nada frente a un entero en una moneda sin
subdivisión. Descartada por simplicidad y por la prohibición explícita que habilita.

## Consecuencias

- Toda aserción de dinero en los tests es exacta: `assert vuelto == 4_500`. `approx`
  sobre dinero queda prohibido — la igualdad aproximada en moneda es un defecto.
- La función de redondeo y la regla de cuadre necesitan tests propios, exhaustivos, antes
  de que exista cualquier cálculo que las use.
- Si algún día el proyecto opera en una moneda con decimales, esto se rompe. Es un costo
  aceptado: el sistema es para Paraguay.
