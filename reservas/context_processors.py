import os


def sitio(request):
    """Datos de contacto y enlaces del sitio. Se leen de variables de entorno (archivo .env) para no escribir enlaces 
    reales en el código. Mientras no estén definidos, se usan marcadores.
    """
    return {
        "sitio": {
            "instagram_url": os.environ.get("INSTAGRAM_URL", "https://www.instagram.com/hospedajepirque/"),
            "whatsapp_url": os.environ.get("WHATSAPP_URL", "#"),
            "maps_url": os.environ.get("GOOGLE_MAPS_URL", "https://maps.app.goo.gl/L36Lf9NzWVyizEZ66"),
            "mapa_embed_url": os.environ.get("MAPA_EMBED_URL", "https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d3321.714242477607!2d-70.5719181!3d-33.6386506!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x9662d62e148fccb7%3A0xb6ca24f08763980d!2sHospedaje%20Rural%20Pirque!5e0!3m2!1ses-419!2scl!4v1792645032077!5m2!1ses-419!2scl"),
            "resenas_url": os.environ.get("RESENAS_URL", "#"),
            "dejar_resena_url": os.environ.get("DEJAR_RESENA_URL", "#"),
            "video_embed_url": os.environ.get("VIDEO_EMBED_URL", ""),
            "email_contacto": os.environ.get("EMAIL_CONTACTO", "correo@ejemplo.cl"),
        }
    }

def contador_admin(request):
    """Cantidad de solicitudes pendientes, solo dentro del admin."""
    user = getattr(request, "user", None)
    if (
        request.path.startswith("/admin/")
        and user is not None
        and user.is_authenticated
        and user.is_staff
    ):
        from .models import SolicitudReserva

        return {
            "solicitudes_pendientes": SolicitudReserva.objects.filter(
                estado=SolicitudReserva.Estado.PENDIENTE
            ).count()
        }
    return {}