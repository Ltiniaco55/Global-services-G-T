"""Formularios de cotización y postulación de empleo.

- TrabajaConNosotrosForm: postulación de empleo, usado en /contacto/ (las
  consultas generales ya no pasan por un formulario — se atienden por
  WhatsApp directamente desde esa misma página).
- CotizacionForm: solicitud formal de cotización, usado en /cotizacion/, con
  un selector de servicios poblado dinámicamente desde sitio/data/servicios.json
  (así nunca hay que tocar este archivo cuando se agregue o cambie un servicio).

Ambos formularios exigen nombre, correo y teléfono válidos antes de poder
enviarse (ver TelefonoValidadoMixin). El teléfono se valida en formato, no
existencia real de la línea — eso requeriría un servicio externo de
verificación, fuera del alcance de este sitio.
"""
import re

from django import forms

from .data_loader import load_servicios

# Acepta un + opcional al inicio, dígitos, espacios, guiones y paréntesis.
# El selector de país (intl-tel-input) del lado del cliente normalmente
# entrega el número ya en formato internacional completo (+58...), pero
# esta validación también deja pasar un número "crudo" por si JavaScript
# no llegó a correr, así el sitio no le bloquea el envío a nadie por eso.
TELEFONO_REGEX = re.compile(r'^\+?[\d\s\-()]{7,20}$')


def validar_telefono(valor):
    valor = (valor or '').strip()
    if not TELEFONO_REGEX.match(valor):
        raise forms.ValidationError('Ingresa un número de teléfono válido.')
    solo_digitos = re.sub(r'\D', '', valor)
    if len(solo_digitos) < 7 or len(solo_digitos) > 15:
        raise forms.ValidationError('Ingresa un número de teléfono válido.')
    return valor


class TelefonoValidadoMixin:
    """Comparten ContactoForm y CotizacionForm: el teléfono es obligatorio
    y debe tener un formato de número válido."""

    def clean_telefono(self):
        return validar_telefono(self.cleaned_data.get('telefono'))


class TrabajaConNosotrosForm(TelefonoValidadoMixin, forms.Form):
    """Postulación de empleo, en la misma página que /contacto/ (tarjeta
    "Trabaja con Nosotros"). El currículum se maneja igual que los adjuntos
    de CotizacionForm (request.FILES en la vista, no un forms.FileField),
    con la diferencia de que acá es obligatorio — se valida en
    sitio/views.py::_validar_cv.

    Campos obligatorios: nombre, correo, teléfono y el currículum. El
    puesto de interés y el mensaje son opcionales.
    """

    nombre = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={'placeholder': 'Nombre y apellido'}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Correo'}),
    )
    telefono = forms.CharField(
        max_length=40,
        widget=forms.TextInput(attrs={'placeholder': 'Teléfono', 'type': 'tel'}),
    )
    puesto_interes = forms.CharField(
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Puesto de interés (opcional)'}),
    )
    mensaje = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Cuéntanos brevemente tu experiencia (opcional)',
            'rows': 4,
        }),
    )

    # --- Honeypot anti-spam ---------------------------------------------
    empresa_web = forms.CharField(required=False, widget=forms.HiddenInput())

    def is_spam(self):
        return bool(self.cleaned_data.get('empresa_web'))


class CotizacionForm(TelefonoValidadoMixin, forms.Form):
    """Solicitud formal de cotización.

    El flujo está inspirado en el formulario de contacto para proveedores
    de Dia (dia.es/contacto-proveedores): datos de contacto, selección de
    categorías/servicios por checkboxes, adjuntos de apoyo, observaciones
    y aceptación de la política de privacidad.

    Campos obligatorios: nombre, correo, teléfono, asunto, al menos un
    servicio y la aceptación de privacidad. El resto (empresa, adjuntos,
    observaciones) es opcional.

    Nota: el campo de archivos adjuntos NO se declara aquí como
    forms.FileField, porque ese campo no soporta selección múltiple de
    forma nativa en Django. Se maneja directamente en la vista leyendo
    request.FILES.getlist('adjuntos') — ver sitio/views.py.
    """

    OTRO = 'otro'

    ASUNTO_MIN_PALABRAS = 3
    ASUNTO_MAX_PALABRAS = 12

    nombre = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={'placeholder': 'Nombre y apellido'}),
    )
    empresa = forms.CharField(
        max_length=120,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Empresa (opcional)'}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Correo'}),
    )
    telefono = forms.CharField(
        max_length=40,
        widget=forms.TextInput(attrs={'placeholder': 'Teléfono / WhatsApp', 'type': 'tel'}),
    )
    asunto = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Asunto'}),
    )
    servicios = forms.MultipleChoiceField(
        label='Servicios de interés',
        widget=forms.CheckboxSelectMultiple,
        error_messages={'required': 'Selecciona al menos un servicio.'},
    )
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'placeholder': 'Cuéntanos más: alcance, ubicación, plazos estimados...',
            'rows': 5,
        }),
    )
    acepta_privacidad = forms.BooleanField(
        label='He leído y acepto la política de privacidad',
        error_messages={'required': 'Debes aceptar la política de privacidad para continuar.'},
    )

    # --- Honeypot anti-spam ---------------------------------------------
    empresa_web = forms.CharField(required=False, widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Las opciones del selector de servicios se arman en cada instancia
        # (no a nivel de clase) para que siempre reflejen el contenido
        # actual de servicios.json sin necesitar un restart del server.
        choices = [(s['slug'], s['titulo']) for s in load_servicios()]
        choices.append((self.OTRO, 'Otro / no estoy seguro'))
        self.fields['servicios'].choices = choices

    def clean_asunto(self):
        # El asunto es una línea corta (para eso está "Observaciones" más
        # abajo, donde sí puede explayarse) — ni una sola palabra vaga ni
        # un párrafo entero.
        valor = self.cleaned_data['asunto'].strip()
        palabras = len(valor.split())
        if palabras < self.ASUNTO_MIN_PALABRAS or palabras > self.ASUNTO_MAX_PALABRAS:
            raise forms.ValidationError(
                f'El asunto debe tener entre {self.ASUNTO_MIN_PALABRAS} y '
                f'{self.ASUNTO_MAX_PALABRAS} palabras.'
            )
        return valor

    def is_spam(self):
        return bool(self.cleaned_data.get('empresa_web'))
