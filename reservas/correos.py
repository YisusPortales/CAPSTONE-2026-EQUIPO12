import hashlib
import logging

from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMessage
from django.utils import translation
from django.utils.formats import date_format
from django.utils.translation import gettext as _

log = logging.getLogger(__name__)

MAX_ACUSES_POR_HORA = 3  # tope por correo de huésped, evita usar el formulario para spamear a terceros


def _enviar(asunto, lineas, destino, responder_a=None):
    """Nunca rompe la petición: si el SMTP falla, queda en el log."""
    try:
        EmailMessage(
            asunto,
            "\n\n".join(lineas),
            settings.DEFAULT_FROM_EMAIL,
            [destino],
            reply_to=[responder_a] if responder_a else None,
        ).send()
    except Exception:
        log.exception("No se pudo enviar el correo %r a %s", asunto, destino)


def _permitido(email):
    clave = "acuse:" + hashlib.sha256(email.lower().encode()).hexdigest()[:24]
    cache.add(clave, 0, 3600)
    try:
        return cache.incr(clave) <= MAX_ACUSES_POR_HORA
    except ValueError:
        return True


def _idioma(s):
    codigo = (s.idioma or "es")[:2]
    return codigo if codigo in ("es", "en", "pt") else "es"


def nueva_solicitud(s):
    """Aviso al administrador (siempre en español) y acuse de recibo al cliente."""
    h = s.huesped
    if settings.NOTIFY_EMAIL:
        _enviar(
            f"Nueva solicitud: {s.nombre_para_mostrar} ({s.fecha_llegada:%d/%m} al {s.fecha_salida:%d/%m})",
            [
                f"Huésped: {s.nombre_para_mostrar} <{h.email}>",
                f"Llegada: {s.fecha_llegada:%d/%m/%Y}  ·  Salida: {s.fecha_salida:%d/%m/%Y}  ·  Personas: {s.personas}",
                "Casa completa: " + ("sí" if s.casa_completa else "no")
                + "  ·  Prefiere WhatsApp: " + ("sí" if s.contactar_por_whatsapp else "no"),
                f"Comentarios: {s.comentarios or '-'}",
                "Revísala en /gestion/.",
            ],
            settings.NOTIFY_EMAIL,
            responder_a=h.email,
        )
    if h.email and _permitido(h.email):
        with translation.override(_idioma(s)):
            _enviar(
                _("Recibimos tu solicitud de reserva"),
                [
                    _("Hola %(nombre)s,") % {"nombre": s.nombre_para_mostrar},
                    _("Recibimos tu solicitud para el %(llegada)s al %(salida)s.") % _fechas(s),
                    _("Noches: %(noches)s · Personas: %(personas)s") % {"noches": s.noches, "personas": s.personas},
                    _("Todavía no es una reserva confirmada: revisaremos la disponibilidad y te responderemos pronto."),
                    _("Si necesitas cambiar algo, responde a este correo."),
                    "Hospedaje Rural Pirque",
                ],
                h.email,
                responder_a=settings.NOTIFY_EMAIL or None,
            )


def estado_cambiado(s):
    """Correo al cliente cuando la solicitud queda confirmada o rechazada."""
    from .models import SolicitudReserva

    h = s.huesped
    if not h.email:
        return
    with translation.override(_idioma(s)):
        if s.estado == SolicitudReserva.Estado.CONFIRMADA:
            asunto = _("Tu reserva fue confirmada")
            cuerpo = [
                _("¡Buenas noticias! Tu solicitud para el %(llegada)s al %(salida)s fue confirmada.") % _fechas(s),
                _("Te contactaremos para coordinar el abono y los detalles de tu llegada."),
            ]
        elif s.estado == SolicitudReserva.Estado.RECHAZADA:
            asunto = _("Sobre tu solicitud de reserva")
            cuerpo = [
                _("Lamentablemente no podemos recibirte entre el %(llegada)s y el %(salida)s.") % _fechas(s),
                _("Si quieres, puedes enviar una nueva solicitud con otras fechas."),
            ]
        else:
            return
        _enviar(
            asunto,
            [_("Hola %(nombre)s,") % {"nombre": s.nombre_para_mostrar}, *cuerpo, "Hospedaje Rural Pirque"],
            h.email,
            responder_a=settings.NOTIFY_EMAIL or None,
        )


def _fechas(s):
    return {
        "llegada": date_format(s.fecha_llegada, "DATE_FORMAT"),
        "salida": date_format(s.fecha_salida, "DATE_FORMAT"),
    }