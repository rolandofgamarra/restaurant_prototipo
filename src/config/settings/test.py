"""Configuracion de test. `pytest-django` usa este modulo (ver `pyproject.toml`).

Ajusta solo lo minimo para que la coleccion y ejecucion de tests arranque. El
reloj fijo, el proveedor de correo en memoria y `task_always_eager` de Celery
(plan §1.12) llegan en T20; `PROVEEDOR_CORREO` / `REMITENTE_COMPROBANTE` llegan
en T56. Esta tarea no los escribe.
"""

from .base import *

DEBUG = False

# El cliente de test de Django hace requests HTTP planas por defecto: forzar HTTPS acá
# rompería cualquier test de vista con un redirect en vez del response esperado. No tiene
# relación con el flag DJANGO_LAN_SIN_TLS de base.py (ese es de despliegue, esto es de test).
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
