from django import template
from django.apps import apps

register = template.Library()

NOMBRES_APP = {"auth": "Cuentas", "reservas": "Reservas", "galeria": "Galería"}

# La pestaña "Galería" es solo un grupo del menú: sus modelos viven en la app "reservas".
APP_REAL = {"galeria": "reservas"}
MODELOS_GALERIA = {"foto", "video"}

DESCRIPCIONES = {
    "Habitacion": "Cuartos del hospedaje, tipo de baño y capacidad.",
    "Huesped": "Personas que han enviado una solicitud de reserva.",
    "Resena": "Opiniones de visitantes. Aprueba las que se publican.",
    "Servicio": "Servicios incluidos y adicionales del hospedaje.",
    "SolicitudReserva": "Solicitudes de estadía: confirma o rechaza.",
    "Foto": "Imágenes de la galería, con su categoría y orden.",
    "Video": "Videos de la galería, subidos como archivo o por enlace.",
    "User": "Cuentas con acceso a este panel.",
}


@register.simple_tag
def nombre_app(app_label, por_defecto=""):
    return NOMBRES_APP.get(app_label, por_defecto)


@register.simple_tag
def total(app_label, object_name):
    try:
        return apps.get_model(APP_REAL.get(app_label, app_label), object_name)._default_manager.count()
    except LookupError:
        return ""


@register.simple_tag
def descripcion(object_name):
    return DESCRIPCIONES.get(object_name, "")


@register.simple_tag(takes_context=True)
def app_actual(context):
    """Pestaña que debe verse marcada según la página en que está el usuario."""
    opts = context.get("opts")
    if opts is not None:
        if opts.app_label == "reservas" and opts.model_name in MODELOS_GALERIA:
            return "galeria"
        return opts.app_label
    return context.get("app_label") or "reservas"