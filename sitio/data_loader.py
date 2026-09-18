"""Carga del contenido dinámico del sitio desde archivos JSON.

Por decisión de proyecto no hay base de datos: servicios, proyectos y
flota viven en sitio/data/*.json y se leen en cada request. Para un sitio
corporativo de este tamaño el costo de leer el JSON en cada vista es
insignificante; si el contenido creciera mucho, aquí es donde se
agregaría cacheo (django.core.cache) sin tocar las views.
"""
import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / 'data'


def _load(filename):
    with open(DATA_DIR / filename, encoding='utf-8') as f:
        return json.load(f)


@lru_cache
def load_servicios():
    return _load('servicios.json')['servicios']


@lru_cache
def load_proyectos():
    return _load('proyectos.json')['proyectos']


@lru_cache
def load_flota():
    return _load('flota.json')


def get_servicio(slug):
    return next((s for s in load_servicios() if s['slug'] == slug and s.get('tiene_detalle')), None)


def get_proyecto(slug):
    return next((p for p in load_proyectos() if p['slug'] == slug), None)
