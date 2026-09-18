"""Configuración WSGI para gyt_django (usada por Gunicorn en producción)."""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gtglobal.settings')

application = get_wsgi_application()
