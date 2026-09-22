"""Tests de humo de shared/result.py — transversal (plan §1.2).

T5 no tiene módulo de test declarado en el plan (la verificación real llega con
los servicios que devuelven `Resultado[T]`, más adelante). Estos tests solo
confirman que `Ok`/`Error` se importan e instancian como se espera.
"""

import dataclasses

import pytest
from src.shared.errors import ErrorDeNegocio
from src.shared.result import Error, Ok


class TestOk:
    def test_ok_guarda_el_valor_y_es_verdadero(self):
        resultado = Ok(42)
        assert resultado.ok is True
        assert resultado.valor == 42

    def test_ok_es_inmutable(self):
        resultado = Ok("algo")
        with pytest.raises(dataclasses.FrozenInstanceError):
            setattr(resultado, "valor", "otro")


class TestError:
    def test_error_guarda_el_error_y_es_falso(self):
        error = ErrorDeNegocio(codigo="SALDO_INSUFICIENTE", mensaje="Saldo insuficiente.")
        resultado = Error(error)
        assert resultado.ok is False
        assert resultado.error is error
