"""Context processor que pone los datos de la empresa (settings.EMPRESA)
disponibles en TODOS los templates como `{{ empresa }}`, sin tener que
pasarlos manualmente en cada view (se usan en el header, footer, menú
burger y el JSON-LD de cada página)."""
from django.conf import settings


def empresa(request):
    return {'empresa': settings.EMPRESA}
