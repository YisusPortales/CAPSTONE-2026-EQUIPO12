from django import forms
from django.contrib import admin, messages
from django.contrib.auth.models import Group
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponseNotAllowed, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.http import url_has_allowed_host_and_scheme

from .admin_utils import AccionesFilaMixin
from .models import Habitacion, Huesped, Resena, Servicio, SolicitudReserva, Foto, CategoriaFoto, Video

admin.site.site_header = "Hospedaje Rural Pirque"
admin.site.site_title = "Administración · Pirque"
admin.site.index_title = "Panel de administración"

# Los grupos de permisos no se usan en este proyecto: se ocultan del panel.
admin.site.unregister(Group)


class ActivacionMixin:
    """Acciones 'Activar' y 'Desactivar' para modelos con un campo booleano."""

    campo_activo = "activa"
    actions = ["activar", "desactivar"]

    @admin.action(description="Activar seleccionados")
    def activar(self, request, queryset):
        n = queryset.update(**{self.campo_activo: True})
        self.message_user(request, f"{n} registro(s) activado(s).", messages.SUCCESS)

    @admin.action(description="Desactivar seleccionados")
    def desactivar(self, request, queryset):
        n = queryset.update(**{self.campo_activo: False})
        self.message_user(request, f"{n} registro(s) desactivado(s).", messages.SUCCESS)


# ---------------------------------------------------------------- Habitaciones
class HabitacionForm(forms.ModelForm):
    class Meta:
        model = Habitacion
        fields = "__all__"
        labels = {
            "tipo_bano": "Tipo de baño",
            "capacidad_ideal": "Capacidad ideal (personas)",
        }


@admin.register(Habitacion)
class HabitacionAdmin(ActivacionMixin, AccionesFilaMixin, admin.ModelAdmin):
    form = HabitacionForm
    list_display = ("nombre", "tipo_de_bano", "capacidad_ideal", "activa", "orden")
    list_filter = ("tipo_bano", "activa")
    search_fields = ("nombre",)

    @admin.display(description="Tipo de baño", ordering="tipo_bano")
    def tipo_de_bano(self, obj):
        return obj.get_tipo_bano_display()


# -------------------------------------------------------------------- Servicios
@admin.register(Servicio)
class ServicioAdmin(ActivacionMixin, AccionesFilaMixin, admin.ModelAdmin):
    campo_activo = "activo"
    list_display = ("nombre", "incluido", "activo", "orden")
    list_filter = ("incluido", "activo")
    search_fields = ("nombre",)


# -------------------------------------------------------------------- Huéspedes
@admin.register(Huesped)
class HuespedAdmin(AccionesFilaMixin, admin.ModelAdmin):
    list_display = ("nombre_completo", "email", "telefono", "creado_en")
    search_fields = ("nombre_completo", "email", "telefono")
    readonly_fields = ("creado_en",)


# ---------------------------------------------------------------------- Reseñas
@admin.register(Resena)
class ResenaAdmin(AccionesFilaMixin, admin.ModelAdmin):
    list_display = ("nombre", "pais", "puntuacion_estrellas", "comentario_corto", "estado_etiqueta", "creada")
    list_filter = ("aprobada", "puntuacion")
    search_fields = ("nombre", "pais", "comentario")
    actions = ["aprobar", "ocultar"]

    @admin.display(description="Puntuación", ordering="puntuacion")
    def puntuacion_estrellas(self, obj):
        return format_html('<span class="estrellas-fijas">{}</span>', obj.estrellas)

    @admin.display(description="Comentario")
    def comentario_corto(self, obj):
        texto = obj.comentario
        return texto if len(texto) <= 80 else texto[:80] + "…"

    @admin.display(description="Estado", ordering="aprobada")
    def estado_etiqueta(self, obj):
        if obj.aprobada:
            return format_html('<span class="pill pill-{}">{}</span>', "confirmada", "Publicada")
        return format_html('<span class="pill pill-{}">{}</span>', "pendiente", "Por aprobar")

    @admin.action(description="Aprobar y publicar seleccionadas")
    def aprobar(self, request, queryset):
        n = queryset.update(aprobada=True)
        self.message_user(request, f"{n} reseña(s) publicada(s).", messages.SUCCESS)

    @admin.action(description="Ocultar seleccionadas")
    def ocultar(self, request, queryset):
        n = queryset.update(aprobada=False)
        self.message_user(request, f"{n} reseña(s) ocultada(s).", messages.SUCCESS)


# ---------------------------------------------------------- Solicitudes de reserva
@admin.register(SolicitudReserva)
class SolicitudReservaAdmin(AccionesFilaMixin, admin.ModelAdmin):
    list_display = (
        "huesped_nombre", "contacto", "llegada", "salida",
        "noches", "personas", "alojamiento", "estado_etiqueta", "responder",
    )
    list_filter = ("estado", "casa_completa", "idioma")
    search_fields = ("huesped__nombre_completo", "huesped__email", "comentarios")
    date_hierarchy = "fecha_llegada"
    actions = ["confirmar", "rechazar", "volver_a_pendiente"]
    readonly_fields = ("creada_en", "actualizada_en")
    filter_horizontal = ("habitaciones",)
    fieldsets = (
        ("Huésped", {"fields": ("huesped", "contactar_por_whatsapp", "idioma")}),
        ("Estadía", {"fields": ("fecha_llegada", "fecha_salida", "personas", "casa_completa", "habitaciones")}),
        ("Detalle", {"fields": ("comentarios",)}),
        ("Gestión", {"fields": ("estado", "creada_en", "actualizada_en")}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("huesped").prefetch_related("habitaciones")

    # ----- Columnas -----
    @admin.display(description="Huésped", ordering="huesped__nombre_completo")
    def huesped_nombre(self, obj):
        return obj.huesped.nombre_completo

    @admin.display(description="Contacto")
    def contacto(self, obj):
        return format_html("{}<br><small>{}</small>", obj.huesped.email, obj.huesped.telefono or "—")

    @admin.display(description="Llegada", ordering="fecha_llegada")
    def llegada(self, obj):
        return obj.fecha_llegada.strftime("%d/%m/%Y")

    @admin.display(description="Salida", ordering="fecha_salida")
    def salida(self, obj):
        return obj.fecha_salida.strftime("%d/%m/%Y")

    @admin.display(description="Alojamiento")
    def alojamiento(self, obj):
        if obj.casa_completa:
            return "Casa completa"
        return ", ".join(h.nombre for h in obj.habitaciones.all()) or "—"

    @admin.display(description="Estado", ordering="estado")
    def estado_etiqueta(self, obj):
        return format_html('<span class="pill pill-{}">{}</span>', obj.estado, obj.get_estado_display())

    @admin.display(description="Responder")
    def responder(self, obj):
        if obj.estado != SolicitudReserva.Estado.PENDIENTE:
            return "—"
        nombre = obj.huesped.nombre_completo
        return format_html(
            '<button type="submit" class="fila-boton ok" formmethod="post" formaction="{}" '
            'data-confirmar="¿Aceptar la solicitud de {}?">Aceptar</button>'
            '<button type="submit" class="fila-boton peligro" formmethod="post" formaction="{}" '
            'data-confirmar="¿Rechazar la solicitud de {}?">Rechazar</button>',
            reverse("admin:reservas_solicitudreserva_aceptar", args=[obj.pk]), nombre,
            reverse("admin:reservas_solicitudreserva_rechazar", args=[obj.pk]), nombre,
        )

    # ----- Botones Aceptar / Rechazar por fila -----
    def get_urls(self):
        propias = [
            path("<int:pk>/aceptar/",
                 self.admin_site.admin_view(self.aceptar_vista),
                 name="reservas_solicitudreserva_aceptar"),
            path("<int:pk>/rechazar/",
                 self.admin_site.admin_view(self.rechazar_vista),
                 name="reservas_solicitudreserva_rechazar"),
        ]
        return propias + super().get_urls()

    def aceptar_vista(self, request, pk):
        return self._responder(request, pk, SolicitudReserva.Estado.CONFIRMADA)

    def rechazar_vista(self, request, pk):
        return self._responder(request, pk, SolicitudReserva.Estado.RECHAZADA)

    def _responder(self, request, pk, nuevo_estado):
        if request.method != "POST":
            return HttpResponseNotAllowed(["POST"])
        if not self.has_change_permission(request):
            raise PermissionDenied

        with transaction.atomic():
            s = get_object_or_404(SolicitudReserva.objects.select_related("huesped"), pk=pk)
            nombre = s.huesped.nombre_completo
            if (
                nuevo_estado == SolicitudReserva.Estado.CONFIRMADA
                and SolicitudReserva.hay_conflicto(s.fecha_llegada, s.fecha_salida, s.pk)
            ):
                self.message_user(
                    request,
                    f"No se pudo aceptar a {nombre}: ya hay una estadía confirmada en esas fechas.",
                    messages.WARNING,
                )
            else:
                s.estado = nuevo_estado
                s.save(update_fields=["estado", "actualizada_en"])
                verbo = "aceptada" if nuevo_estado == SolicitudReserva.Estado.CONFIRMADA else "rechazada"
                self.message_user(request, f"Solicitud de {nombre} {verbo}.", messages.SUCCESS)

        destino = request.META.get("HTTP_REFERER", "")
        if not url_has_allowed_host_and_scheme(
            destino, allowed_hosts={request.get_host()}, require_https=request.is_secure()
        ):
            destino = reverse("admin:reservas_solicitudreserva_changelist")
        return HttpResponseRedirect(destino)

    # ----- Acciones masivas (barra flotante) -----
    @admin.action(description="Confirmar solicitudes seleccionadas")
    def confirmar(self, request, queryset):
        confirmadas = 0
        for s in queryset.exclude(estado=SolicitudReserva.Estado.CONFIRMADA):
            if SolicitudReserva.hay_conflicto(s.fecha_llegada, s.fecha_salida, s.pk):
                self.message_user(
                    request,
                    f"No se pudo confirmar a {s.huesped.nombre_completo} "
                    f"({s.fecha_llegada:%d/%m} al {s.fecha_salida:%d/%m}): ya hay una estadía confirmada.",
                    messages.WARNING,
                )
                continue
            s.estado = SolicitudReserva.Estado.CONFIRMADA
            s.save(update_fields=["estado", "actualizada_en"])
            confirmadas += 1
        if confirmadas:
            self.message_user(request, f"{confirmadas} solicitud(es) confirmada(s).", messages.SUCCESS)

    @admin.action(description="Rechazar solicitudes seleccionadas")
    def rechazar(self, request, queryset):
        n = queryset.update(estado=SolicitudReserva.Estado.RECHAZADA, actualizada_en=timezone.now())
        self.message_user(request, f"{n} solicitud(es) rechazada(s).", messages.SUCCESS)

    @admin.action(description="Volver a pendiente")
    def volver_a_pendiente(self, request, queryset):
        n = queryset.update(estado=SolicitudReserva.Estado.PENDIENTE, actualizada_en=timezone.now())
        self.message_user(request, f"{n} solicitud(es) devuelta(s) a pendiente.", messages.SUCCESS)

@admin.register(Foto)
class FotoAdmin(admin.ModelAdmin):
    list_display = ("miniatura", "descripcion", "categoria", "orden", "activa", "creada")
    list_display_links = ("miniatura",)
    list_editable = ("categoria", "orden", "activa")
    list_filter = ("categoria", "activa")
    search_fields = ("descripcion",)

    @admin.display(description="Foto")
    def miniatura(self, obj):
        if not obj.imagen:
            return "—"
        return format_html(
            '<img src="{}" alt="" style="height:56px;width:84px;object-fit:cover;border-radius:6px;">',
            obj.imagen.url,
        )


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "orden", "activo", "creado")
    list_editable = ("orden", "activo")
    list_filter = ("activo",)
    fields = ("titulo", "archivo", "enlace", "portada", "orden", "activo")

    @admin.display(description="Video")
    def nombre(self, obj):
        return obj.titulo or obj.enlace or obj.archivo.name

    @admin.display(description="Tipo")
    def tipo(self, obj):
        if obj.archivo:
            return "Archivo"
        return obj.proveedor.capitalize() or "—"