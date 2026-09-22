"""Jerarquía base de errores de negocio (transversal, plan §1.2).

`ErrorDeNegocio` hereda de `Exception`: se puede lanzar con `raise` y capturar
con `except ErrorDeNegocio`. `Resultado[T]` (ver `shared/result.py`) sigue
siendo el mecanismo preferido para el flujo de negocio esperado en general
(saldo insuficiente, motivo de anulación inválido, exceso en un medio no
efectivo, etc.), pero no son mutuamente excluyentes: cada servicio/RF elige
el mecanismo que le quede mejor, y el pseudocódigo de otras secciones del
plan (§3.3, §3.4) ya usa `lanzar ExcesoNoEfectivo(...)`, `lanzar SinSesion`,
`lanzar PinBloqueado`, etc. directamente como excepciones.

Las subclases concretas (`SaldoInsuficiente`, `ExcesoNoEfectivo`, etc., ver
`domain/errores.py`) agregan los campos propios de cada caso sobre esta base.
"""

from __future__ import annotations


class ErrorDeNegocio(Exception):
    """Error de negocio esperado, lanzable con `raise`/`except`.

    `codigo` es estable y pensado para lógica (comparaciones, tests, logs);
    `mensaje` ya está en español de Paraguay, listo para mostrarse en la UI.
    """

    def __init__(self, codigo: str, mensaje: str) -> None:
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje
