"""Pruebas del sitio: páginas en los dos idiomas, sitemap, robots, admin
oculto y los formularios de cotización y postulación.

Se ejecutan con "python manage.py test". No sale ninguna petición real a
la red: Resend (requests.post) y Vercel Blob (BlobClient) van simulados.

El runner de Django fuerza DEBUG=False antes de cargar las URLs, así que
/admin/ se prueba igual que en producción aunque el .env local tenga
DJANGO_DEBUG=True. Todas las peticiones se hacen como HTTPS (secure=True)
para que funcionen también si SECURE_SSL_REDIRECT está activo.
"""
import json
import warnings
from unittest import mock

import requests
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, SimpleTestCase, override_settings
from django.urls import reverse
from django.utils import translation

from .data_loader import _load, load_proyectos, load_servicios

IDIOMAS = ('es', 'en')
PAGINAS = ['home', 'flota', 'servicios', 'proyectos', 'contacto', 'cotizacion',
           'cotizacion_gracias', 'privacidad', 'aviso_legal']
# Páginas que no van en el sitemap (formularios y la de "gracias").
PAGINAS_FUERA_DEL_SITEMAP = 3


def _primer_servicio():
    return next(s['slug'] for s in load_servicios() if s.get('tiene_detalle'))


def _urls(idioma):
    """Todas las URLs públicas del sitio en un idioma."""
    with translation.override(idioma):
        urls = [reverse(f'sitio:{nombre}') for nombre in PAGINAS]
        urls += [reverse('sitio:servicio_detalle', kwargs={'slug': s['slug']})
                 for s in load_servicios() if s.get('tiene_detalle')]
        urls += [reverse('sitio:proyecto_detalle', kwargs={'slug': p['slug']}) for p in load_proyectos()]
    return urls


class SitioTestCase(SimpleTestCase):
    """Base: cliente que siempre pide por HTTPS, como llega el tráfico en Vercel."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # WhiteNoise avisa de que no existe staticfiles/ (solo se genera con
        # collectstatic en el build); acá no se prueban los estáticos.
        cls.enterClassContext(warnings.catch_warnings())
        warnings.filterwarnings('ignore', message='No directory at', category=UserWarning)

    def get(self, url, **extra):
        return self.client.get(url, secure=True, **extra)

    def post(self, url, datos=None, **extra):
        return self.client.post(url, datos or {}, secure=True, **extra)


class PaginasTests(SitioTestCase):
    def test_todas_las_paginas_responden_200_en_su_idioma(self):
        for idioma in IDIOMAS:
            for url in _urls(idioma):
                with self.subTest(idioma=idioma, url=url):
                    respuesta = self.get(url)
                    self.assertEqual(respuesta.status_code, 200)
                    self.assertContains(respuesta, f'lang="{idioma}"')

    def test_espanol_sin_prefijo_e_ingles_bajo_en(self):
        self.assertFalse([u for u in _urls('es') if u.startswith('/en/')])
        self.assertFalse([u for u in _urls('en') if not u.startswith('/en/')])
        self.assertEqual(len(_urls('es')), len(_urls('en')))

    def test_cotizacion_preselecciona_el_servicio_de_la_url(self):
        slug = _primer_servicio()
        for idioma in IDIOMAS:
            with self.subTest(idioma=idioma):
                with translation.override(idioma):
                    url = reverse('sitio:cotizacion')
                respuesta = self.get(f'{url}?servicio={slug}')
                self.assertEqual(respuesta.status_code, 200)
                self.assertEqual(respuesta.context['form'].initial, {'servicios': [slug]})

    def test_alias_de_servicio_redirige_a_la_url_nueva(self):
        alias = _load('servicios', 'es').get('alias', {})
        for viejo, nuevo in alias.items():
            with self.subTest(alias=viejo):
                respuesta = self.get(f'/servicios/{viejo}/')
                self.assertRedirects(
                    respuesta, f'/servicios/{nuevo}/', status_code=301, fetch_redirect_response=False,
                )

    def test_404_propia_en_cada_idioma(self):
        for idioma, url in (('es', '/no-existe/'), ('en', '/en/does-not-exist/')):
            with self.subTest(idioma=idioma):
                respuesta = self.get(url)
                self.assertEqual(respuesta.status_code, 404)
                self.assertTemplateUsed(respuesta, '404.html')
                self.assertContains(respuesta, f'lang="{idioma}"', status_code=404)

    def test_admin_no_existe_con_debug_false(self):
        self.assertFalse(settings.DEBUG)
        for url in ('/admin/', '/admin/login/', '/en/admin/'):
            with self.subTest(url=url):
                self.assertEqual(self.get(url).status_code, 404)


class SeoTests(SitioTestCase):
    def test_sitemap(self):
        respuesta = self.get('/sitemap.xml')
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta['Content-Type'].startswith('application/xml'))
        xml = respuesta.content.decode()
        esperadas = sum(len(_urls(idioma)) - PAGINAS_FUERA_DEL_SITEMAP for idioma in IDIOMAS)
        self.assertEqual(xml.count('<url>'), esperadas)
        self.assertIn('<loc>https://testserver/servicios/</loc>', xml)
        self.assertIn('<loc>https://testserver/en/services/</loc>', xml)
        for hreflang in ('es', 'en', 'x-default'):
            self.assertIn(f'hreflang="{hreflang}"', xml)

    def test_robots(self):
        respuesta = self.get('/robots.txt')
        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(respuesta['Content-Type'].startswith('text/plain'))
        self.assertContains(respuesta, 'Sitemap: https://testserver/sitemap.xml')


class ResendRoto(Exception):
    pass


@override_settings(RESEND_API_KEY='clave-de-prueba', BLOB_READ_WRITE_TOKEN='token-de-prueba')
class FormulariosTests(SitioTestCase):
    """Los dos formularios comparten el mismo flujo de entrega (correo por
    Resend y, si falla, respaldo en Blob), así que cada prueba recorre los
    dos formularios en los dos idiomas."""

    # tipo de lead -> (nombre de la ruta, campo de archivos, nº de archivos)
    FORMULARIOS = {
        'cotizacion': ('sitio:cotizacion', 'adjuntos', 2),
        'postulacion': ('sitio:contacto', 'cv', 1),
    }

    def setUp(self):
        # Ninguna prueba debe poder llegar a la red: los dos clientes van
        # simulados siempre. autospec valida las llamadas contra la firma
        # real del SDK de Vercel.
        self.resend = self.enterContext(mock.patch('sitio.views.requests.post'))
        self.blob_cls = self.enterContext(mock.patch('sitio.respaldo.BlobClient', autospec=True))
        self.blob = self.blob_cls.return_value.__enter__.return_value

    def resend_falla(self):
        self.resend.return_value.raise_for_status.side_effect = requests.HTTPError('500 Server Error')

    def datos(self, tipo):
        if tipo == 'cotizacion':
            return {
                'nombre': 'Ana <Pérez>', 'empresa': 'ACME & Co', 'email': 'ana@example.com',
                'telefono': '+58 412 555 1234', 'asunto': 'Cotización de izaje pesado',
                'servicios': [_primer_servicio(), 'otro'], 'observaciones': 'Línea 1\nLínea 2',
                'acepta_privacidad': 'on', 'empresa_web': '',
                'adjuntos': [
                    SimpleUploadedFile('plano uno.pdf', b'%PDF-plano'),
                    SimpleUploadedFile('foto.png', b'PNG-foto'),
                ],
            }
        return {
            'nombre': 'Luis Gómez', 'email': 'luis@example.com', 'telefono': '+58 414 555 9876',
            'puesto_interes': 'Operador', 'mensaje': 'Diez años de experiencia',
            'acepta_privacidad': 'on', 'empresa_web': '',
            'cv': SimpleUploadedFile('cv.pdf', b'%PDF-cv'),
        }

    def casos(self):
        """Recorre (idioma, tipo de lead) con los simulacros limpios en cada vuelta."""
        for idioma in IDIOMAS:
            for tipo, (ruta, campo_archivos, n_archivos) in self.FORMULARIOS.items():
                with translation.override(idioma):
                    url = reverse(ruta)
                    gracias = reverse('sitio:cotizacion_gracias')
                self.resend.reset_mock(return_value=True, side_effect=True)
                self.blob_cls.reset_mock()
                self.blob.put.side_effect = None
                with self.subTest(idioma=idioma, tipo=tipo):
                    yield idioma, tipo, url, gracias, campo_archivos, n_archivos

    def assertErrorGeneral(self, respuesta):
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'role="alert"')
        self.assertContains(respuesta, 'WhatsApp')

    def test_resend_funciona(self):
        for idioma, tipo, url, gracias, _campo, n_archivos in self.casos():
            respuesta = self.post(url, self.datos(tipo))
            self.assertRedirects(respuesta, gracias, fetch_redirect_response=False)

            self.resend.assert_called_once()
            self.assertEqual(self.resend.call_args.args[0], 'https://api.resend.com/emails')
            self.assertEqual(self.resend.call_args.kwargs['headers']['Authorization'], 'Bearer clave-de-prueba')
            payload = self.resend.call_args.kwargs['json']
            self.assertEqual(payload['to'], [settings.CONTACTO_EMAIL_DESTINO])
            self.assertEqual(len(payload['attachments']), n_archivos)
            # El correo va siempre en español e indica el idioma del visitante.
            idioma_visitante = {'es': 'Español', 'en': 'Inglés'}[idioma]
            self.assertIn(f'Idioma del formulario: {idioma_visitante}', payload['text'])
            # El respaldo solo se usa si el correo falla.
            self.blob_cls.assert_not_called()

    def test_el_html_del_correo_escapa_lo_que_escribe_el_visitante(self):
        self.post(reverse('sitio:cotizacion'), self.datos('cotizacion'))
        cuerpo_html = self.resend.call_args.kwargs['json']['html']
        self.assertIn('Ana &lt;Pérez&gt;', cuerpo_html)
        self.assertIn('ACME &amp; Co', cuerpo_html)
        self.assertNotIn('<Pérez>', cuerpo_html)

    def test_resend_falla_y_el_lead_se_guarda_en_blob(self):
        for _idioma, tipo, url, gracias, _campo, n_archivos in self.casos():
            self.resend_falla()
            with self.assertLogs('sitio.views', level='ERROR'), self.assertLogs('sitio.respaldo', level='WARNING'):
                respuesta = self.post(url, self.datos(tipo))
            # El lead no se perdió: el visitante ve la página de gracias.
            self.assertRedirects(respuesta, gracias, fetch_redirect_response=False)

            self.blob_cls.assert_called_once_with(token='token-de-prueba')
            llamadas = self.blob.put.call_args_list
            self.assertEqual(len(llamadas), n_archivos + 1)
            for llamada in llamadas:
                self.assertRegex(llamada.args[0], rf'^leads/\d{{4}}-\d\d-\d\d/\d{{6}}-{tipo}-[0-9a-f]{{8}}/')
                self.assertEqual(llamada.kwargs['access'], 'private')
            # Resend ya leyó los archivos hasta el final: tienen que llegar enteros.
            for llamada in llamadas[:-1]:
                self.assertIn('/adjuntos/', llamada.args[0])
                self.assertTrue(llamada.args[1].startswith((b'%PDF', b'PNG')))

            self.assertTrue(llamadas[-1].args[0].endswith('/lead.json'))
            lead = json.loads(llamadas[-1].args[1].decode('utf-8'))
            self.assertEqual(lead['tipo'], tipo)
            self.assertEqual(lead['datos']['email'], self.datos(tipo)['email'])
            self.assertNotIn('empresa_web', lead['datos'])
            self.assertEqual(lead['adjuntos'], [llamada.args[0] for llamada in llamadas[:-1]])
            self.assertEqual(lead['adjuntos_no_guardados'], [])

    def test_resend_falla_por_error_de_red(self):
        for _idioma, tipo, url, gracias, _campo, _n in self.casos():
            self.resend.side_effect = requests.ConnectionError('sin red')
            with self.assertLogs('sitio.views', level='ERROR'), self.assertLogs('sitio.respaldo', level='WARNING'):
                respuesta = self.post(url, self.datos(tipo))
            self.assertRedirects(respuesta, gracias, fetch_redirect_response=False)
            self.assertTrue(self.blob.put.call_args.args[0].endswith('/lead.json'))

    def test_resend_y_blob_fallan(self):
        for _idioma, tipo, url, _gracias, _campo, _n in self.casos():
            self.resend_falla()
            self.blob.put.side_effect = ResendRoto('Blob caído')
            with self.assertLogs('sitio.views', level='ERROR'), self.assertLogs('sitio.respaldo', level='ERROR'):
                respuesta = self.post(url, self.datos(tipo))
            self.assertErrorGeneral(respuesta)

    def test_resend_falla_y_un_adjunto_no_se_puede_guardar(self):
        """Si solo falla un archivo, el lead se guarda igual y deja anotado cuál falta."""
        self.resend_falla()
        self.blob.put.side_effect = [ResendRoto('Blob caído'), None, None]
        with self.assertLogs('sitio.views', level='ERROR'), self.assertLogs('sitio.respaldo', level='ERROR'):
            respuesta = self.post(reverse('sitio:cotizacion'), self.datos('cotizacion'))
        self.assertRedirects(respuesta, reverse('sitio:cotizacion_gracias'), fetch_redirect_response=False)
        lead = json.loads(self.blob.put.call_args.args[1].decode('utf-8'))
        self.assertEqual(lead['adjuntos_no_guardados'], ['plano uno.pdf'])
        self.assertEqual(len(lead['adjuntos']), 1)

    @override_settings(BLOB_READ_WRITE_TOKEN='')
    def test_resend_falla_sin_respaldo_configurado(self):
        for _idioma, tipo, url, _gracias, _campo, _n in self.casos():
            self.resend_falla()
            with self.assertLogs('sitio.views', level='ERROR'), self.assertLogs('sitio.respaldo', level='ERROR'):
                respuesta = self.post(url, self.datos(tipo))
            self.assertErrorGeneral(respuesta)
            self.blob_cls.assert_not_called()

    def test_honeypot_no_envia_nada(self):
        for _idioma, tipo, url, gracias, _campo, _n in self.casos():
            datos = self.datos(tipo)
            datos['empresa_web'] = 'https://spam.example'
            respuesta = self.post(url, datos)
            self.assertRedirects(respuesta, gracias, fetch_redirect_response=False)
            self.resend.assert_not_called()
            self.blob_cls.assert_not_called()

    def test_formulario_vacio_muestra_errores(self):
        for _idioma, _tipo, url, _gracias, _campo, _n in self.casos():
            respuesta = self.post(url)
            self.assertEqual(respuesta.status_code, 200)
            self.assertContains(respuesta, 'form-error')
            self.resend.assert_not_called()

    def test_archivo_con_extension_no_permitida(self):
        for _idioma, tipo, url, _gracias, campo_archivos, _n in self.casos():
            datos = self.datos(tipo)
            datos[campo_archivos] = SimpleUploadedFile('programa.exe', b'MZ')
            respuesta = self.post(url, datos)
            self.assertEqual(respuesta.status_code, 200)
            self.assertContains(respuesta, 'role="alert"')
            self.resend.assert_not_called()

    def test_postulacion_exige_curriculum(self):
        datos = self.datos('postulacion')
        del datos['cv']
        respuesta = self.post(reverse('sitio:contacto'), datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'role="alert"')
        self.resend.assert_not_called()

    def test_telefono_y_asunto_invalidos(self):
        datos = self.datos('cotizacion')
        datos.update(telefono='abc', asunto='Hola')
        respuesta = self.post(reverse('sitio:cotizacion'), datos)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(set(respuesta.context['form'].errors), {'telefono', 'asunto'})
        self.resend.assert_not_called()

    def test_csrf(self):
        """El POST exige el token CSRF, también por HTTPS (con su Referer)."""
        url = reverse('sitio:cotizacion')
        cliente = Client(enforce_csrf_checks=True)
        token = cliente.get(url, secure=True).cookies['csrftoken'].value

        datos = self.datos('cotizacion')
        datos['csrfmiddlewaretoken'] = token
        respuesta = cliente.post(url, datos, secure=True, headers={'referer': f'https://testserver{url}'})
        self.assertRedirects(respuesta, reverse('sitio:cotizacion_gracias'), fetch_redirect_response=False)
        self.resend.assert_called_once()

        self.resend.reset_mock()
        with self.assertLogs('django.security.csrf', level='WARNING'):
            respuesta = Client(enforce_csrf_checks=True).post(url, self.datos('cotizacion'), secure=True)
        self.assertEqual(respuesta.status_code, 403)
        self.resend.assert_not_called()


class PrivacidadTests(SitioTestCase):
    """La política de privacidad tiene que existir en los dos idiomas, estar
    enlazada desde el footer y contar lo que la web hace de verdad con los
    datos (correo por Resend y respaldo en Vercel Blob)."""

    # Lo que debe decir la política en cada idioma.
    CONTENIDO = {
        'es': ('Política de Privacidad', 'currículum', 'Resend', 'Vercel Blob', 'almacenamiento privado',
               '90 días', 'Legislación aplicable'),
        'en': ('Privacy Policy', 'résumé', 'Resend', 'Vercel Blob', 'private storage',
               '90 days', 'Applicable law'),
    }

    def url_privacidad(self, idioma):
        with translation.override(idioma):
            return reverse('sitio:privacidad')

    def test_responde_200_en_los_dos_idiomas(self):
        self.assertEqual(self.url_privacidad('es'), '/privacidad/')
        self.assertEqual(self.url_privacidad('en'), '/en/privacy/')
        for idioma in IDIOMAS:
            with self.subTest(idioma=idioma):
                respuesta = self.get(self.url_privacidad(idioma))
                self.assertEqual(respuesta.status_code, 200)
                self.assertTemplateUsed(respuesta, 'sitio/privacidad.html')
                self.assertContains(respuesta, f'lang="{idioma}"')

    def test_explica_que_se_hace_con_los_datos(self):
        for idioma, textos in self.CONTENIDO.items():
            respuesta = self.get(self.url_privacidad(idioma))
            for texto in textos:
                with self.subTest(idioma=idioma, texto=texto):
                    self.assertContains(respuesta, texto)

    def test_muestra_responsable_y_contacto(self):
        for idioma in IDIOMAS:
            with self.subTest(idioma=idioma):
                respuesta = self.get(self.url_privacidad(idioma))
                for dato in ('rif', 'direccion', 'email', 'telefono'):
                    self.assertContains(respuesta, settings.EMPRESA[dato])

    def test_la_version_en_ingles_esta_traducida_entera(self):
        """Las dos versiones tienen los mismos apartados y ninguno se queda en español."""
        es = self.get(self.url_privacidad('es'))
        en = self.get(self.url_privacidad('en'))
        self.assertEqual(es.content.count(b'<h2'), en.content.count(b'<h2'))
        self.assertEqual(es.content.count(b'<li>'), en.content.count(b'<li>'))
        for texto in ('Responsable', 'Qué datos', 'Cuánto tiempo', 'Tus derechos', 'Legislación'):
            with self.subTest(texto=texto):
                self.assertNotContains(en, texto)

    def test_el_footer_enlaza_a_la_politica_en_todas_las_paginas(self):
        for idioma in IDIOMAS:
            enlace = f'<a href="{self.url_privacidad(idioma)}">{self.CONTENIDO[idioma][0]}</a>'
            for url in _urls(idioma):
                with self.subTest(idioma=idioma, url=url):
                    html_pagina = self.get(url).content.decode()
                    footer = html_pagina[html_pagina.index('<footer'):html_pagina.index('</footer>')]
                    self.assertIn(enlace, footer)
