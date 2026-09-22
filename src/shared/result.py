"""`Resultado[T]`: éxito o error de negocio, sin lanzar excepciones (transversal, plan §1.2).

Los servicios de `domain`/`services` devuelven `Resultado[T]` en vez de lanzar
excepciones para el flujo de negocio esperado en general (plan §1.2). Se
modela como una unión discriminada de dos variantes inmutables, `Ok[T]` y
`Error`, en vez de un único tipo con atributos opcionales (`valor: T | None`,
`error: ErrorDeNegocio | None`): así es imposible construir a nivel de tipos
un estado inválido (éxito con error, o error sin `ErrorDeNegocio`), y mypy
estricto puede angostar (`narrow`) el tipo de `resultado` a partir de
`resultado.ok` en un `if`.

`Error` no es genérica en `T`: un error de negocio no lleva el valor exitoso,
así que no necesita cargar ese parámetro de tipo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from src.shared.errors import ErrorDeNegocio


@dataclass(frozen=True, slots=True)
class Ok[T]:
    """Resultado exitoso: contiene el valor `valor` de tipo `T`.

    `ok` no es parámetro del constructor (`init=False`): siempre vale `True`,
    así que no existe forma de construir un `Ok(valor, ok=False)` inválido.
    """

    valor: T
    ok: Literal[True] = field(default=True, init=False)


@dataclass(frozen=True, slots=True)
class Error:
    """Resultado fallido: contiene un `ErrorDeNegocio`.

    `ok` no es parámetro del constructor (`init=False`): siempre vale `False`,
    simétrico con `Ok` (evita `Error(e, ok=True)` en runtime).
    """

    error: ErrorDeNegocio
    ok: Literal[False] = field(default=False, init=False)


type Resultado[T] = Ok[T] | Error
