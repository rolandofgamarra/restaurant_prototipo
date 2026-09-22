"""Configuracion ASGI para el proyecto `restaurant`."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.config.settings.base")

application = get_asgi_application()
