import logging
import os

from django.conf import settings
from django.core.mail import EmailMessage
from django.http import Http404
from django.shortcuts import redirect, render

from .data_loader import get_proyecto, get_servicio, load_flota, load_proyectos, load_servicios
from .forms import CotizacionForm, TrabajaConNosotrosForm

logger = logging.getLogger(__name__)

# Extensiones permitidas para los adjuntos de /cotizacion/ y tamaño total
# máximo (en bytes) — pensado para planos, fotos y fichas técnicas, no
# para archivos ejecutables ni comprimidos sin revisar.
ADJUNTOS_EXTENSIONES_PERMITIDAS = {
    '.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx', '.xls', '.xlsx', '.dwg', '.dxf',
}
ADJUNTOS_TAMANO_MAXIMO = 15 * 1024 * 1024  # 15 MB entre todos los archivos

# Currículum del formulario "Trabaja con Nosotros" (en /contacto/): un solo
# archivo, formatos de documento únicamente (no hace falta aceptar planos
# ni imágenes acá) y obligatorio, a diferencia de los adjuntos de arriba.
CV_EXTENSIONES_PERMITIDAS = {'.pdf', '.doc', '.docx'}
CV_TAMANO_MAXIMO = 8 * 1024 * 1024  # 8 MB


def _enviar_notificacion(asunto, cuerpo, adjuntos=None):
    """Envía el correo de notificación de un lead (contacto o cotización),
    adjuntando los archivos que haya (si los hay).

    Devuelve True si se envió bien, False si falló (y deja el error
    logueado) — así cada vista solo decide qué hacer con el resultado, sin
    repetir el try/except del envío.
    """
    try:
        email = EmailMessage(
            subject=asunto,
            body=cuerpo,
            from_email=None,  # usa DEFAULT_FROM_EMAIL
            to=[settings.CONTACTO_EMAIL_DESTINO],
        )
        for archivo in (adjuntos or []):
            email.attach(archivo.name, archivo.read(), archivo.content_type)
        email.send(fail_silently=False)
        return True
    except Exception:
        logger.exception('Fallo al enviar el correo de notificación')
        return False


def _validar_adjuntos(archivos):
    """Valida los archivos adjuntos del formulario de cotización.

    No es un campo de CotizacionForm porque forms.FileField no soporta
    selección múltiple de forma nativa — se valida a mano acá. Devuelve un
    mensaje de error (str) si algo no cumple, o None si todo está bien.
    """
    if not archivos:
        return None
    tamano_total = 0
    for archivo in archivos:
        ext = os.path.splitext(archivo.name)[1].lower()
        if ext not in ADJUNTOS_EXTENSIONES_PERMITIDAS:
            return (
                f'El archivo "{archivo.name}" tiene un formato no permitido. '
                'Formatos aceptados: PDF, imágenes (JPG/PNG), Word, Excel y planos (DWG/DXF).'
            )
        tamano_total += archivo.size
    if tamano_total > ADJUNTOS_TAMANO_MAXIMO:
        return 'Los archivos adjuntos superan el tamaño máximo permitido (15 MB en total).'
    return None


def _validar_cv(archivos):
    """Valida el currículum del formulario "Trabaja con Nosotros".

    A diferencia de _validar_adjuntos, acá el archivo es obligatorio (una
    postulación sin currículum no tiene mucho sentido) y solo se acepta
    uno solo, en formato PDF o Word. Devuelve un mensaje de error (str) si
    algo no cumple, o None si todo está bien.
    """
    if not archivos:
        return 'Adjunta tu currículum para poder enviar tu postulación.'
    if len(archivos) > 1:
        return 'Adjunta un solo archivo con tu currículum.'
    archivo = archivos[0]
    ext = os.path.splitext(archivo.name)[1].lower()
    if ext not in CV_EXTENSIONES_PERMITIDAS:
        return (
            f'El archivo "{archivo.name}" tiene un formato no permitido. '
            'Formatos aceptados para el currículum: PDF o Word (.doc, .docx).'
        )
    if archivo.size > CV_TAMANO_MAXIMO:
        return 'El currículum supera el tamaño máximo permitido (8 MB).'
    return None


def home(request):
    """Homepage. La sección #contacto es ahora solo un teaser que enlaza a
    /contacto/ y /cotizacion/ (páginas propias, ver las vistas contacto()
    y cotizacion() más abajo) — ya no procesa ningún formulario aquí."""
    return render(request, 'sitio/homepage.html', {
        'servicios': load_servicios(),
        'proyectos': load_proyectos(),
    })


def contacto(request):
    """Página de contacto: información de contacto (teléfono, WhatsApp,
    correo, ubicación) para consultas generales, y el formulario de
    postulación de empleo "Trabaja con Nosotros". Ya no hay un formulario
    de contacto general — las consultas generales se atienden por
    WhatsApp, directamente desde esta misma página."""
    form_trabajo = TrabajaConNosotrosForm()

    if request.method == 'POST':
        form_trabajo = TrabajaConNosotrosForm(request.POST)
        cv = request.FILES.getlist('cv')
        error_cv = _validar_cv(cv)
        form_trabajo_valido = form_trabajo.is_valid()

        if error_cv:
            form_trabajo.add_error(None, error_cv)

        if form_trabajo_valido and not error_cv:
            if form_trabajo.is_spam():
                logger.info('Postulación de empleo descartada por honeypot.')
                return redirect('sitio:cotizacion_gracias')

            cd = form_trabajo.cleaned_data
            cuerpo = (
                f"Nombre: {cd['nombre']}\n"
                f"Correo: {cd['email']}\n"
                f"Teléfono: {cd['telefono']}\n"
                f"Puesto de interés: {cd['puesto_interes'] or '(no indicado)'}\n\n"
                f"Mensaje:\n{cd['mensaje'] or '(sin mensaje)'}"
            )
            if _enviar_notificacion(f"Nueva postulación de empleo — {cd['nombre']}", cuerpo, cv):
                return redirect('sitio:cotizacion_gracias')
            form_trabajo.add_error(
                None,
                'No se pudo enviar tu postulación en este momento. '
                'Intenta de nuevo o escríbenos directamente por WhatsApp.',
            )

    return render(request, 'sitio/contacto.html', {'form_trabajo': form_trabajo})


def cotizacion(request):
    """Solicitud formal de cotización — mismo flujo que el formulario de
    contacto para proveedores de Dia: datos de contacto, servicios de
    interés (checkboxes, selección múltiple), archivos adjuntos,
    observaciones y aceptación de privacidad.

    Soporta preselección de un servicio vía ?servicio=<slug> (usado por el
    CTA "Cotizar este servicio" en cada página de detalle de servicio)."""
    if request.method == 'POST':
        form = CotizacionForm(request.POST)
        adjuntos = request.FILES.getlist('adjuntos')
        error_adjuntos = _validar_adjuntos(adjuntos)
        form_valido = form.is_valid()

        if error_adjuntos:
            form.add_error(None, error_adjuntos)

        if form_valido and not error_adjuntos:
            if form.is_spam():
                logger.info('Envío de cotización descartado por honeypot.')
                return redirect('sitio:cotizacion_gracias')

            cd = form.cleaned_data
            servicios_map = dict(form.fields['servicios'].choices)
            servicios_titulo = ', '.join(servicios_map.get(s, s) for s in cd['servicios'])
            cuerpo = (
                f"Nombre: {cd['nombre']}\n"
                f"Empresa: {cd['empresa'] or '(no indicada)'}\n"
                f"Correo: {cd['email']}\n"
                f"Teléfono: {cd['telefono'] or '(no indicado)'}\n"
                f"Asunto: {cd['asunto']}\n"
                f"Servicios de interés: {servicios_titulo}\n\n"
                f"Observaciones:\n{cd['observaciones'] or '(sin observaciones)'}"
            )
            if _enviar_notificacion(f"Nueva solicitud de cotización — {cd['nombre']}", cuerpo, adjuntos):
                return redirect('sitio:cotizacion_gracias')
            form.add_error(
                None,
                'No se pudo enviar tu solicitud en este momento. '
                'Intenta de nuevo o escríbenos directamente por WhatsApp.',
            )
    else:
        slug_preseleccionado = request.GET.get('servicio')
        initial = {}
        if slug_preseleccionado and get_servicio(slug_preseleccionado):
            initial['servicios'] = [slug_preseleccionado]
        form = CotizacionForm(initial=initial)

    return render(request, 'sitio/cotizacion.html', {'form': form})


def privacidad(request):
    return render(request, 'sitio/privacidad.html')


def flota(request):
    data = load_flota()
    return render(request, 'sitio/flota.html', {
        'embarcaciones': data['embarcaciones'],
        'capacidades': data['capacidades'],
    })


def servicios(request):
    return render(request, 'sitio/servicios.html', {
        'servicios': load_servicios(),
    })


def servicio_detalle(request, slug):
    servicio = get_servicio(slug)
    if servicio is None:
        raise Http404('Servicio no encontrado')
    return render(request, 'sitio/servicio_detalle.html', {'servicio': servicio})


def proyectos(request):
    return render(request, 'sitio/proyectos.html', {
        'proyectos': load_proyectos(),
    })


def proyecto_detalle(request, slug):
    proyecto = get_proyecto(slug)
    if proyecto is None:
        raise Http404('Proyecto no encontrado')
    return render(request, 'sitio/proyecto_detalle.html', {'proyecto': proyecto})


def cotizacion_gracias(request):
    return render(request, 'sitio/cotizacion_gracias.html')


def error_404(request, exception=None):
    response = render(request, '404.html', status=404)
    return response
