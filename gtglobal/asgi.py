"""Configuración ASGI para gyt_django (no imprescindible para este sitio, se
incluye porque Django la genera por defecto)."""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gtglobal.settings')

application = get_asgi_application()
