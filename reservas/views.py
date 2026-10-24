from datetime import date

from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
from django.db.models import Avg
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .forms import ResenaForm, SolicitudReservaForm
from .models import Resena, SolicitudReserva


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


def resenas(request):
    if request.method == "POST":
        form = ResenaForm(request.POST)
        if form.is_valid():
            if not form.cleaned_data["sitio_web"]:  # si está lleno, es un bot
                form.save()  # aprobada=False por defecto
            return redirect(f"{reverse('reservas:resenas')}?enviada=1")
    else:
        form = ResenaForm()

    aprobadas = Resena.objects.filter(aprobada=True)
    return render(request, "reservas/resenas.html", {
        "form": form,
        "resenas": aprobadas,
        "promedio": aprobadas.aggregate(p=Avg("puntuacion"))["p"],
        "enviada": request.GET.get("enviada") == "1",
    })


# ---------------------------------------------------------------------------
# Panel de gestión (solo personal autorizado)
# ---------------------------------------------------------------------------

ACCIONES_SOLICITUD = {
    "confirmar": SolicitudReserva.Estado.CONFIRMADA,
    "rechazar": SolicitudReserva.Estado.RECHAZADA,
    "reabrir": SolicitudReserva.Estado.PENDIENTE,
}


def _resumen():
    hoy = timezone.localdate()
    return {
        "n_pendientes": SolicitudReserva.objects.filter(
            estado=SolicitudReserva.Estado.PENDIENTE
        ).count(),
        "n_resenas_pendientes": Resena.objects.filter(aprobada=False).count(),
        "proximas": SolicitudReserva.objects.filter(
            estado=SolicitudReserva.Estado.CONFIRMADA, fecha_salida__gte=hoy
        ).select_related("huesped").order_by("fecha_llegada")[:5],
    }


def _con_conflicto(solicitud):
    """Marca si una solicitud pendiente se cruza con una estadía ya confirmada."""
    solicitud.conflicto = (
        solicitud.estado == SolicitudReserva.Estado.PENDIENTE
        and SolicitudReserva.hay_conflicto(
            solicitud.fecha_llegada, solicitud.fecha_salida, solicitud.pk
        )
    )
    return solicitud


@staff_member_required
def gestion(request):
    estado = request.GET.get("estado", SolicitudReserva.Estado.PENDIENTE)
    solicitudes = SolicitudReserva.objects.select_related("huesped").prefetch_related(
        "habitaciones"
    )
    if estado in SolicitudReserva.Estado.values:
        solicitudes = solicitudes.filter(estado=estado)
    else:
        estado = "todas"
    orden = "creada_en" if estado == SolicitudReserva.Estado.PENDIENTE else "-creada_en"
    solicitudes = [_con_conflicto(s) for s in solicitudes.order_by(orden)[:50]]
    return render(request, "reservas/gestion.html", {
        "solicitudes": solicitudes,
        "resenas": Resena.objects.order_by("aprobada", "-creada")[:30],
        "estado": estado,
        "estados": SolicitudReserva.Estado.choices,
        **_resumen(),
    })


@staff_member_required
@require_POST
def gestion_solicitud(request, pk, accion):
    if accion not in ACCIONES_SOLICITUD:
        raise Http404
    error = ""
    with transaction.atomic():
        solicitud = get_object_or_404(
            SolicitudReserva.objects.select_related("huesped"), pk=pk
        )
        nuevo = ACCIONES_SOLICITUD[accion]
        if nuevo == SolicitudReserva.Estado.CONFIRMADA and SolicitudReserva.hay_conflicto(
            solicitud.fecha_llegada, solicitud.fecha_salida, solicitud.pk
        ):
            error = "No se puede confirmar: ya hay una estadía confirmada en esas fechas."
        else:
            solicitud.estado = nuevo
            solicitud.save(update_fields=["estado", "actualizada_en"])
    return render(request, "reservas/_gestion_solicitud.html", {
        "s": _con_conflicto(solicitud), "error": error, "oob": True, **_resumen(),
    })


@staff_member_required
@require_POST
def gestion_resena(request, pk, accion):
    resena = get_object_or_404(Resena, pk=pk)
    if accion == "eliminar":
        resena.delete()
        return render(request, "reservas/_gestion_resena.html", {
            "eliminada": True, "oob": True, **_resumen(),
        })
    if accion in ("aprobar", "ocultar"):
        resena.aprobada = accion == "aprobar"
        resena.save(update_fields=["aprobada"])
        return render(request, "reservas/_gestion_resena.html", {
            "r": resena, "oob": True, **_resumen(),
        })
    raise Http404