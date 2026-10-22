from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from datetime import date
from .models import SolicitudReserva
from .forms import SolicitudReservaForm


@require_http_methods(["GET", "POST"])
def solicitar_reserva(request):
    """Página de inicio: contiene el sitio y el formulario de reserva."""
    if request.method == "POST":
        form = SolicitudReservaForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirigir tras guardar evita reenviar el formulario al recargar.
            return redirect("reservas:gracias")
    else:
        form = SolicitudReservaForm()
    return render(request, "reservas/inicio.html", {"form": form})


@require_http_methods(["GET"])
def gracias(request):
    return render(request, "reservas/gracias.html")

@require_http_methods(["GET"])
def disponibilidad(request):
    """Devuelve un aviso breve (HTML) según las fechas elegidas. Lo usa htmx."""
    try:
        llegada = date.fromisoformat(request.GET.get("fecha_llegada", ""))
        salida = date.fromisoformat(request.GET.get("fecha_salida", ""))
    except ValueError:
        # Faltan fechas o están incompletas: no se muestra nada.
        return render(request, "reservas/_disponibilidad.html", {"estado": ""})

    if salida <= llegada:
        estado = "invalido"
    elif SolicitudReserva.hay_conflicto(llegada, salida):
        estado = "ocupado"
    else:
        estado = "libre"
    return render(request, "reservas/_disponibilidad.html", {"estado": estado})
