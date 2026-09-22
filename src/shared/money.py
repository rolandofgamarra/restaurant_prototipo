"""Único punto de redondeo monetario del sistema (ADR 0002).

Todos los montos son guaraníes enteros (`int`). Nunca se usa `float` ni
`Decimal` para dinero: el redondeo comercial (mitad hacia arriba) se hace
con aritmética entera exacta.
"""


def redondear_gs(monto: int, multiplo: int) -> int:
    """Redondea `monto` al múltiplo `multiplo` más cercano (mitad hacia arriba).

    Si `multiplo <= 1`, devuelve `monto` sin modificar.
    """
    if multiplo <= 1:
        return monto
    resto = monto % multiplo
    if resto * 2 >= multiplo:
        return monto - resto + multiplo
    return monto - resto
