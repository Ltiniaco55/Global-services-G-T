#!/bin/bash
# Script de build que corre Vercel antes de desplegar: instala deps y
# genera static/ -> staticfiles/ (whitenoise los sirve desde ahi).
# Misma version de Python que la funcion (ver .python-version). El venv va
# en /tmp para que no acabe dentro del bundle de la funcion.
set -e
python3.12 -m venv /tmp/venv-build
/tmp/venv-build/bin/python -m pip install -r requirements.txt
/tmp/venv-build/bin/python manage.py collectstatic --noinput --clear