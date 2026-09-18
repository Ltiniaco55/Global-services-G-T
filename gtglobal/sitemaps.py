"""Sitemap del sitio, generado con django.contrib.sitemaps.

Incluye las páginas estáticas y las páginas de detalle dinámicas
(servicios y proyectos que sí tienen ficha propia), leyendo los mismos
JSON que usan las views.
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from sitio.data_loader import load_proyectos, load_servicios


class PaginasEstaticasSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.8

    def items(self):
        return [
            'sitio:home',
            'sitio:servicios',
            'sitio:flota',
            'sitio:proyectos',
        ]

    def location(self, item):
        return reverse(item)

    def priority(self, item):
        return 1.0 if item == 'sitio:home' else 0.8


class ServiciosDetalleSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        return [s for s in load_servicios() if s.get('tiene_detalle')]

    def location(self, item):
        return reverse('sitio:servicio_detalle', kwargs={'slug': item['slug']})


class ProyectosDetalleSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6

    def items(self):
        return load_proyectos()

    def location(self, item):
        return reverse('sitio:proyecto_detalle', kwargs={'slug': item['slug']})


sitemaps = {
    'paginas': PaginasEstaticasSitemap,
    'servicios': ServiciosDetalleSitemap,
    'proyectos': ProyectosDetalleSitemap,
}
