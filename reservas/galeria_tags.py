from django import template

register = template.Library()


@register.filter
def partir(valor, separador=","):
    """Convierte 'a.jpg,b.jpg' en ['a.jpg', 'b.jpg']."""
    return [p.strip() for p in str(valor).split(separador) if p.strip()]