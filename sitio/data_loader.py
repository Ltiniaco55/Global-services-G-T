"""Carga del contenido dinámico del sitio desde archivos JSON.

Por decisión de proyecto no hay base de datos: servicios, proyectos y
flota viven en sitio/data/*.json y se leen en cada request. Para un sitio
corporativo de este tamaño el costo de leer el JSON en cada vista es
insignificante; si el contenido creciera mucho, aquí es donde se
agregaría cacheo (django.core.cache) sin tocar las views.

Idiomas: el contenido en español vive en servicios.json, proyectos.json y
flota.json. La versión en inglés está en archivos hermanos con el código
del idioma (servicios.en.json, ...), con la misma estructura y los mismos
slugs. Si falta el archivo de un idioma se usa el español, así una
traducción incompleta nunca rompe la página.
"""
import json
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.utils.translation import get_language

DATA_DIR = Path(__file__).resolve().parent / 'data'


def _idioma():
    """Código corto del idioma activo ('es', 'en'), o el idioma por defecto."""
    return (get_language() or settings.LANGUAGE_CODE).split('-')[0]


@lru_cache
def _load(nombre, idioma):
    """Lee sitio/data/<nombre>.<idioma>.json, o <nombre>.json (español)
    si es el idioma por defecto o no existe la traducción."""
    ruta = DATA_DIR / f'{nombre}.{idioma}.json'
    if idioma == settings.LANGUAGE_CODE or not ruta.exists():
        ruta = DATA_DIR / f'{nombre}.json'
    with open(ruta, encoding='utf-8') as f:
        return json.load(f)


def load_servicios():
    return _load('servicios', _idioma())['servicios']


def load_proyectos():
    return _load('proyectos', _idioma())['proyectos']


def load_flota():
    return _load('flota', _idioma())


def get_servicio(slug):
    return next((s for s in load_servicios() if s['slug'] == slug and s.get('tiene_detalle')), None)


def get_proyecto(slug):
    return next((p for p in load_proyectos() if p['slug'] == slug), None)
