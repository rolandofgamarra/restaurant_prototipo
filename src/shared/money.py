"""Único punto de redondeo monetario del sistema (ADR 0002).

Todos los montos son guaraníes enteros (`int`). Nunca se usa `float` ni
`Decimal` para dinero: el redondeo comercial (mitad hacia arriba) se hace
con aritmética entera exacta.
"""

from src.shared.errors import ErrorDeNegocio


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


def cuadrar_lineas(total_objetivo: int, totales_linea: list[int]) -> list[int]:
    """Ajusta `totales_linea` para que su suma iguale exactamente `total_objetivo`.

    ADR 0002 §3: se redondea el TOTAL y se ajusta la ÚLTIMA línea (nunca las
    demás, nunca se recalcula el total a partir de las líneas). Invariante del
    plan §3.1: lista vacía exige `total_objetivo == 0` (no puede haber un
    total sin ninguna línea que lo respalde).

    Levanta `ErrorDeNegocio` si el ajuste dejaría la última línea negativa, o
    si la lista está vacía con `total_objetivo != 0`: ambos son error de
    datos, no un caso silencioso a tolerar.
    """
    if not totales_linea:
        if total_objetivo != 0:
            raise ErrorDeNegocio(
                codigo="CUADRE_SIN_LINEAS",
                mensaje=(
                    f"No se puede cuadrar un total de {total_objetivo} Gs sin "
                    "ninguna línea que lo respalde."
                ),
            )
        return []
    suma = sum(totales_linea)
    diferencia = total_objetivo - suma
    ajustadas = list(totales_linea)
    ajustadas[-1] += diferencia
    if ajustadas[-1] < 0:
        raise ErrorDeNegocio(
            codigo="CUADRE_LINEA_NEGATIVA",
            mensaje=(
                f"No se puede cuadrar el total de {total_objetivo} Gs: el ajuste "
                f"dejaría la última línea en {ajustadas[-1]} Gs (negativo). "
                f"Líneas originales: {totales_linea}."
            ),
        )
    return ajustadas
