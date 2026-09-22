"""Tests de humo de shared/errors.py — transversal (plan §1.2).

T5 no tiene módulo de test declarado en el plan (ver test_result.py). Estos
tests confirman que `ErrorDeNegocio` expone `codigo` y `mensaje` en español,
y que además es una `Exception` real: se puede lanzar con `raise` y capturar
con `except ErrorDeNegocio`.
"""

import pytest
from src.shared.errors import ErrorDeNegocio


class TestErrorDeNegocio:
    def test_expone_codigo_y_mensaje(self):
        error = ErrorDeNegocio(codigo="CAJA_CERRADA", mensaje="Debe abrirse la caja.")
        assert error.codigo == "CAJA_CERRADA"
        assert error.mensaje == "Debe abrirse la caja."

    def test_se_puede_lanzar_y_capturar_como_excepcion(self):
        with pytest.raises(ErrorDeNegocio) as info:
            raise ErrorDeNegocio(codigo="CAJA_CERRADA", mensaje="Debe abrirse la caja.")

        error = info.value
        assert error.codigo == "CAJA_CERRADA"
        assert error.mensaje == "Debe abrirse la caja."
