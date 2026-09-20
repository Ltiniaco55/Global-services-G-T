"""
Configuración de Django para gyt_django (G&T Global Service, C.A.)

Migrado desde el sitio estático en public/ — sin base de datos, sin apps de
usuarios. El contenido dinámico (servicios, proyectos, flota) vive en
archivos JSON dentro de sitio/data/. Ver ../MIGRACION.md para el contexto
completo de la migración.
"""
from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Seguridad ---------------------------------------------------------
# SECRET_KEY, DEBUG y ALLOWED_HOSTS SIEMPRE desde variables de entorno.
# Nunca hardcodees estos valores ni los subas a git (usa .env, que está
# en .gitignore; .env.example muestra qué variables hacen falta).
SECRET_KEY = config('DJANGO_SECRET_KEY')
DEBUG = config('DJANGO_DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

# Dominios (con esquema https://) desde los que se aceptan POST — necesario
# para que el formulario de cotizacion/contacto funcione detras de Vercel.
CSRF_TRUSTED_ORIGINS = config('DJANGO_CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

# --- Apps ---------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'sitio',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gtglobal.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'sitio.context_processors.empresa',
            ],
        },
    },
]

WSGI_APPLICATION = 'gtglobal.wsgi.application'

# --- Base de datos --------------------------------------------------------
# Sin base de datos por decisión de proyecto: el contenido viene de JSON
# (sitio/data/*.json). Se deja sqlite3 mínimo solo porque Django necesita
# ALGUNA base de datos configurada para correr migrate en apps internas
# (sessions, admin) si algún día se usan — no se usa para contenido del sitio.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_PASSWORD_VALIDATORS = []

# --- Internacionalización ------------------------------------------------
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Caracas'
USE_I18N = True
USE_TZ = True

# --- Archivos estáticos ----------------------------------------------------
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles' / 'static'  # nested para que coincida con la ruta /static/ de vercel.json

# WhiteNoise sirve los estaticos directamente desde la app WSGI (necesario
# en Vercel, que no tiene un servidor de archivos estaticos aparte).
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Resend (envío de notificaciones de formularios) -----------------------
# API key de Resend (resend.com) y remitente verificado ahí. Nunca
# hardcodees la API key ni la subas a git.
RESEND_API_KEY = config('RESEND_API_KEY', default='')
RESEND_FROM_EMAIL = config('RESEND_FROM_EMAIL', default='onboarding@resend.dev')

# A dónde llegan los leads de los formularios (cotización y postulaciones).
CONTACTO_EMAIL_DESTINO = config('CONTACTO_EMAIL_DESTINO', default='gtglobalservice2014@gmail.com')

# --- Ajustes de seguridad para producción -----------------------------------
# Se activan solos cuando DEBUG=False (o sea, en producción). En local con
# DEBUG=True no molestan (HTTPS no existe en localhost).
# Vercel (como cualquier proxy) termina el HTTPS y reenvia por HTTP interno,
# indicando el protocolo original en este header. Sin esto, Django no se
# entera de que la conexion ya es HTTPS y SECURE_SSL_REDIRECT entra en un
# loop infinito de redirects.
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

if not DEBUG:
    SECURE_SSL_REDIRECT = config('DJANGO_SECURE_SSL_REDIRECT', default=True, cast=bool)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# --- Datos de la empresa (usados en el JSON-LD LocalBusiness, footer, etc.) -
EMPRESA = {
    'nombre': 'G&T Global Service, C.A.',
    'telefono': '0261-4189710',
    'telefono_whatsapp': '+34637054468',
    'email': 'tiniacoluciano05@gmail.com',
    'direccion': 'Av. 4 Bella Vista, Edificio Ferley, Piso PB, Local 1',
    'ciudad': 'Maracaibo',
    'estado': 'Zulia',
    'pais': 'VE',
    'instagram': 'https://instagram.com/gytglobalservice',
    'instagram_handle': '@gytglobalservice',
    # Coordenadas aproximadas de Bella Vista, Maracaibo — ajusta a la
    # ubicación exacta de la sede cuando la tengas georreferenciada.
    'lat': '10.6666',
    'lng': '-71.6125',
}
