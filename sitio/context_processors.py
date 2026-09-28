"""Context processor que pone los datos de la empresa (settings.EMPRESA)
disponibles en TODOS los templates como `{{ empresa }}`, sin tener que
pasarlos manualmente en cada view (se usan en el header, footer, menú
burger y el JSON-LD de cada página)."""
from django.conf import settings


def empresa(request):
    return {'empresa': settings.EMPRESA}


def idiomas(request):
    """URLs de la página actual en cada idioma, para el selector ES/EN del
    header y las etiquetas <link rel="alternate" hreflang> de base.html.

    translate_url() resuelve la URL actual y la vuelve a construir en el
    otro idioma (ej. /servicios/ <-> /en/services/). Si la ruta no se
    puede resolver (una 404, por ejemplo) devuelve la misma URL.
    """
    from django.urls import translate_url

    rutas = {}
    for codigo, nombre in settings.LANGUAGES:
        ruta = translate_url(request.path, codigo)
        rutas[codigo] = {
            'codigo': codigo,
            'nombre': nombre,
            # Para el selector conservamos la query (?servicio=...).
            'url': translate_url(request.get_full_path(), codigo),
            'url_absoluta': request.build_absolute_uri(ruta),
        }
    return {
        'idiomas_pagina': list(rutas.values()),
        'url_x_default': rutas[settings.LANGUAGE_CODE]['url_absoluta'],
    }
