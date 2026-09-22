#!/usr/bin/env python
"""Utilidad de linea de comandos de Django para tareas administrativas."""

import os
import sys


def main() -> None:
    """Ejecutar tareas administrativas."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.config.settings.base")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "No se pudo importar Django. ¿Esta activado el entorno virtual "
            "y estan instaladas las dependencias?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
