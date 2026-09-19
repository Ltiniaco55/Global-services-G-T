"""Punto de entrada WSGI para Vercel (@vercel/python).

Vercel busca un objeto callable llamado "app" en este archivo — es lo
mismo que gtglobal/wsgi.py (usado por Gunicorn), solo que con el nombre
que espera Vercel.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gtglobal.settings')

from django.core.wsgi import get_wsgi_application  # noqa: E402

app = get_wsgi_application()
