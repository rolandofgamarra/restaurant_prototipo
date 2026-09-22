"""Configuracion base de Django, comun a todos los entornos.

Los valores sensibles (clave secreta, base de datos) se leen de variables de
entorno via `pydantic-settings`, coherentes con `.env.example` y
`docker-compose.yml`. Nunca se hardcodean credenciales reales ni `DEBUG=True`.
"""

import secrets
from pathlib import Path
from urllib.parse import urlparse

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Env(BaseSettings):
    """Variables de entorno del proyecto (ver `.env.example`).

    Lee `.env` en la raíz del proyecto si existe (nunca commiteado, ver
    `.gitignore`). `DATABASE_URL` no tiene default: si falta, arranca falla
    fuerte en vez de conectar en silencio contra una base equivocada. Sin
    `DJANGO_SECRET_KEY` en el entorno, se genera una al vuelo (misma receta
    que sugiere `.env.example`); sirve para `manage.py check` y para tests,
    producción siempre la fija por env.
    """

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    django_secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(50))
    django_debug: bool = False
    django_allowed_hosts: str = "localhost,127.0.0.1"
    database_url: str
    django_lan_sin_tls: bool = False


env = Env()

_db_url = urlparse(env.database_url)

SECRET_KEY = env.django_secret_key

DEBUG = env.django_debug

ALLOWED_HOSTS = [host.strip() for host in env.django_allowed_hosts.split(",") if host.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "src.accounts",
    "src.audit",
    "src.cash",
    "src.sync",
    "src.orders",
    "src.notifications",
    "src.payments",
    "src.inventory",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "src.config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "src.config.wsgi.application"
ASGI_APPLICATION = "src.config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": (_db_url.path or "/restaurant").lstrip("/"),
        "USER": _db_url.username or "restaurant",
        "PASSWORD": _db_url.password or "",
        "HOST": _db_url.hostname or "localhost",
        "PORT": _db_url.port or 5432,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "es-py"

TIME_ZONE = "America/Asuncion"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Seguro por defecto (nube, panel admin remoto). El edge box del local habla con las
# cajas por LAN, sin certificado TLS propio (ADR 0001) — su despliegue fija
# DJANGO_LAN_SIN_TLS=true para no forzar HTTPS ni cookies "secure" en esa red interna.
# Ver docs/DEPLOYMENT.md. No confundir con DEBUG: esto es sobre transporte, no logging.
if env.django_lan_sin_tls:
    SECURE_SSL_REDIRECT = False
    SECURE_HSTS_SECONDS = 0
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
else:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
