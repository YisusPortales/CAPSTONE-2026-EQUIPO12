from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
 
from .forms import SolicitudReservaForm
 
 
@require_http_methods(["GET", "POST"])
def solicitar_reserva(request):
    if request.method == "POST":
        form = SolicitudReservaForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirigir tras guardar evita reenviar el formulario al recargar.
            return redirect("reservas:gracias")
    else:
        form = SolicitudReservaForm()
    return render(request, "reservas/solicitar.html", {"form": form})
 
 
@require_http_methods(["GET"])
def gracias(request):
    return render(request, "reservas/gracias.html")