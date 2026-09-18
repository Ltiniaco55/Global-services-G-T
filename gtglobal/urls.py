"""URLs raíz de gyt_django."""
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from .sitemaps import sitemaps

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('sitio.urls')),
    path(
        'sitemap.xml',
        sitemap,
        {'sitemaps': sitemaps},
        name='django.contrib.sitemaps.views.sitemap',
    ),
    path(
        'robots.txt',
        TemplateView.as_view(template_name='robots.txt', content_type='text/plain'),
        name='robots_txt',
    ),
]

# Página 404 con el mismo estilo del sitio (ver sitio/views.py).
handler404 = 'sitio.views.error_404'
