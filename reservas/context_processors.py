import os


def sitio(request):
    """Datos de contacto y enlaces del sitio. Se leen de variables de entorno (archivo .env) para no escribir enlaces 
    reales en el código. Mientras no estén definidos, se usan marcadores.
    """
    return {
        "sitio": {
            "instagram_url": os.environ.get("INSTAGRAM_URL", "https://www.instagram.com/hospedajepirque/"),
            "whatsapp_url": os.environ.get("WHATSAPP_URL", "#"),
            "maps_url": os.environ.get("GOOGLE_MAPS_URL", "#"),
            "mapa_embed_url": os.environ.get("MAPA_EMBED_URL", ""),
            "resenas_url": os.environ.get("RESENAS_URL", "#"),
            "dejar_resena_url": os.environ.get("DEJAR_RESENA_URL", "#"),
            "video_embed_url": os.environ.get("VIDEO_EMBED_URL", ""),
            "email_contacto": os.environ.get("EMAIL_CONTACTO", "correo@ejemplo.cl"),
        }
    }
