from django import template
from django.apps import apps

register = template.Library()

NOMBRES_APP = {"auth": "Cuentas", "reservas": "Reservas"}

DESCRIPCIONES = {
    "Habitacion": "Cuartos del hospedaje, tipo de baño y capacidad.",
    "Huesped": "Personas que han enviado una solicitud de reserva.",
    "Resena": "Opiniones de visitantes. Aprueba las que se publican.",
    "Servicio": "Servicios incluidos y adicionales del hospedaje.",
    "SolicitudReserva": "Solicitudes de estadía: confirma o rechaza.",
    "User": "Cuentas con acceso a este panel.",
}


@register.simple_tag
def nombre_app(app_label, por_defecto=""):
    return NOMBRES_APP.get(app_label, por_defecto)


@register.simple_tag
def total(app_label, object_name):
    try:
        return apps.get_model(app_label, object_name)._default_manager.count()
    except LookupError:
        return ""


@register.simple_tag
def descripcion(object_name):
    return DESCRIPCIONES.get(object_name, "")