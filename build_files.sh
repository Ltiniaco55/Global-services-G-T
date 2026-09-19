#!/bin/bash
# Script de build que corre Vercel antes de desplegar: instala deps y
# genera static/ -> staticfiles/ (whitenoise los sirve desde ahi).
set -e
python3.9 -m pip install -r requirements.txt
python3.9 manage.py collectstatic --noinput --clear
