"""URLs raíz de gyt_django."""
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path
from django.views.generic import TemplateView

from .sitemaps import sitemaps

urlpatterns = [
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

# El admin solo existe en desarrollo: el sitio no tiene modelos propios y en
# Vercel la base de datos no persiste, así que en producción /admin/ da 404.
if settings.DEBUG:
    urlpatterns.append(path('admin/', admin.site.urls))

# Páginas del sitio en los dos idiomas: español sin prefijo (/servicios/,
# igual que antes, así no se rompe ningún enlace ya indexado) e inglés
# bajo /en/ (/en/services/). Las rutas traducidas están en sitio/urls.py.
urlpatterns += i18n_patterns(
    path('', include('sitio.urls')),
    prefix_default_language=False,
)

# Página 404 con el mismo estilo del sitio (ver sitio/views.py).
handler404 = 'sitio.views.error_404'
