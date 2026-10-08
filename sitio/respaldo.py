"""Respaldo de leads en Vercel Blob para cuando falla el envío por Resend.

Sin esto, un lead (cotización o postulación) cuyo correo no sale se
perdía: en Vercel el disco es efímero y no hay base de datos. Acá se
guarda en un store PRIVADO de Vercel Blob (trae currículums y datos
personales, nunca debe ser público):

    leads/<AAAA-MM-DD>/<HHMMSS>-<tipo>-<id>/lead.json
    leads/<AAAA-MM-DD>/<HHMMSS>-<tipo>-<id>/adjuntos/<n>-<archivo>

Se consultan desde el panel de Vercel (Storage -> el store -> Browser).

Usa el SDK oficial de Vercel (paquete "vercel", requiere Python >= 3.10).
"""
import json
import logging
import os
import re
import uuid

from django.conf import settings
from django.utils import timezone
from vercel.blob import BlobClient

logger = logging.getLogger(__name__)

# El SDK reintenta 10 veces por defecto, con esperas cada vez más largas:
# si Blob está caído, el visitante se quedaría esperando hasta que la
# función de Vercel agotara su tiempo. Con 2 reintentos basta. El SDK solo
# deja configurarlo con esta variable de entorno.
os.environ.setdefault('VERCEL_BLOB_RETRIES', '2')


def guardar_lead(tipo, asunto, cuerpo, datos, adjuntos=None):
    """Guarda un lead (y sus archivos) en el respaldo.

    Devuelve True si los datos del lead quedaron guardados, False si no (y
    deja el error logueado). Si lo único que falla es algún adjunto, el
    lead se guarda igual y el JSON indica qué archivos faltan, para poder
    pedírselos de nuevo al cliente.
    """
    if not settings.BLOB_READ_WRITE_TOKEN:
        logger.error('Respaldo de leads sin configurar: falta BLOB_READ_WRITE_TOKEN.')
        return False

    ahora = timezone.localtime()
    carpeta = f'leads/{ahora:%Y-%m-%d}/{ahora:%H%M%S}-{tipo}-{uuid.uuid4().hex[:8]}'

    guardados = []
    no_guardados = []
    try:
        with BlobClient(token=settings.BLOB_READ_WRITE_TOKEN) as cliente:
            for n, archivo in enumerate(adjuntos or [], start=1):
                # El nombre lo elige el visitante: se deja solo lo seguro para una ruta.
                nombre = re.sub(r'[^\w.\-]', '_', archivo.name)[-100:]
                ruta = f'{carpeta}/adjuntos/{n}-{nombre}'
                try:
                    # El envío por Resend ya leyó el archivo hasta el final.
                    archivo.seek(0)
                    cliente.put(ruta, archivo.read(), access='private', content_type='application/octet-stream')
                    guardados.append(ruta)
                except Exception:
                    logger.exception('Fallo al guardar un adjunto en el respaldo de leads')
                    no_guardados.append(archivo.name)

            lead = {
                'tipo': tipo,
                'fecha': ahora.isoformat(timespec='seconds'),
                'asunto': asunto,
                'datos': datos,
                'cuerpo': cuerpo,
                'adjuntos': guardados,
                'adjuntos_no_guardados': no_guardados,
            }
            cliente.put(
                f'{carpeta}/lead.json',
                json.dumps(lead, ensure_ascii=False, indent=2).encode('utf-8'),
                access='private',
                content_type='application/json',
            )
    except Exception:
        logger.exception('Fallo al guardar el lead en el respaldo')
        return False

    # Único aviso de que hay un lead esperando en el respaldo: el correo no
    # salió, así que hay que verlo en los logs de Vercel.
    logger.warning('El correo no se pudo enviar: lead guardado en el respaldo (%s).', carpeta)
    return True
