"""URLs raíz de gyt_django."""
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from .sitemaps import sitemaps

urlpatterns = [
    path('admin/', admin.site.urls),
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

# Páginas del sitio en los dos idiomas: español sin prefijo (/servicios/,
# igual que antes, así no se rompe ningún enlace ya indexado) e inglés
# bajo /en/ (/en/services/). Las rutas traducidas están en sitio/urls.py.
urlpatterns += i18n_patterns(
    path('', include('sitio.urls')),
    prefix_default_language=False,
)

# Página 404 con el mismo estilo del sitio (ver sitio/views.py).
handler404 = 'sitio.views.error_404'
