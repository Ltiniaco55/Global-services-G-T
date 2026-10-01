from django.urls import path
from django.utils.translation import gettext_lazy as _

from . import views

app_name = 'sitio'

# Las rutas están marcadas para traducción: en español se usan tal cual
# (/servicios/) y en inglés salen de locale/en/LC_MESSAGES/django.po
# (/en/services/). Los slugs de servicios y proyectos se mantienen iguales
# en los dos idiomas.
urlpatterns = [
    path('', views.home, name='home'),
    path(_('flota/'), views.flota, name='flota'),
    path(_('servicios/'), views.servicios, name='servicios'),
    path(_('servicios/<slug:slug>/'), views.servicio_detalle, name='servicio_detalle'),
    path(_('proyectos/'), views.proyectos, name='proyectos'),
    path(_('proyectos/<slug:slug>/'), views.proyecto_detalle, name='proyecto_detalle'),
    path(_('contacto/'), views.contacto, name='contacto'),
    path(_('cotizacion/'), views.cotizacion, name='cotizacion'),
    path(_('cotizacion/gracias/'), views.cotizacion_gracias, name='cotizacion_gracias'),
    path(_('privacidad/'), views.privacidad, name='privacidad'),
    path(_('aviso-legal/'), views.aviso_legal, name='aviso_legal'),
]
