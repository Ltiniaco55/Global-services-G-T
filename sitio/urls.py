from django.urls import path

from . import views

app_name = 'sitio'

urlpatterns = [
    path('', views.home, name='home'),
    path('flota/', views.flota, name='flota'),
    path('servicios/', views.servicios, name='servicios'),
    path('servicios/<slug:slug>/', views.servicio_detalle, name='servicio_detalle'),
    path('proyectos/', views.proyectos, name='proyectos'),
    path('proyectos/<slug:slug>/', views.proyecto_detalle, name='proyecto_detalle'),
    path('contacto/', views.contacto, name='contacto'),
    path('cotizacion/', views.cotizacion, name='cotizacion'),
    path('cotizacion/gracias/', views.cotizacion_gracias, name='cotizacion_gracias'),
    path('privacidad/', views.privacidad, name='privacidad'),
]
