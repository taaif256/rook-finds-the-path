"""
Django settings for the Chessboard Robot Navigation Visualizer API.

The API is stateless: board state is never persisted, so no database,
sessions, authentication, or admin site is configured. Runtime options can be
overridden with environment variables (see ``backend/.env.example``).
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_list(name: str, default: str) -> list[str]:
    """Read a comma-separated environment variable into a list of strings."""
    return [item.strip() for item in os.environ.get(name, default).split(",") if item.strip()]


# --- Core -------------------------------------------------------------------

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "dev-only-insecure-key-change-me-before-deploying",
)
DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() in {"1", "true", "yes"}
ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,[::1]")

# --- Applications -----------------------------------------------------------

INSTALLED_APPS = [
    "corsheaders",
    "rest_framework",
    "apps.pathfinding",
]

# CsrfViewMiddleware is intentionally omitted: the API is stateless JSON with
# no cookie/session authentication, so there is no CSRF attack surface.
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # must precede CommonMiddleware
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Database ---------------------------------------------------------------

# No persistence in the initial version; Django falls back to a dummy backend.
DATABASES: dict = {}

# --- CORS -------------------------------------------------------------------

# Origins of the Angular dev server (`ng serve` defaults to port 4200).
CORS_ALLOWED_ORIGINS = _env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:4200,http://127.0.0.1:4200",
)
CORS_URLS_REGEX = r"^/api/.*$"

# --- Django REST Framework --------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
    # django.contrib.auth is not installed, so there is no AnonymousUser model.
    "UNAUTHENTICATED_USER": None,
}

# --- Internationalisation ---------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
