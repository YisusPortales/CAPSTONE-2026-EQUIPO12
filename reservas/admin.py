from django.contrib import admin
from .models import Habitacion, Huesped, Servicio, SolicitudReserva, Resena

admin.site.site_header = "Hospedaje Rural Pirque"
admin.site.site_title = "Administración · Pirque"
admin.site.index_title = "Panel de administración"

@admin.register(Habitacion)
class HabitacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo_bano", "capacidad_ideal", "activa", "orden")
    list_filter = ("tipo_bano", "activa")


@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "incluido", "activo", "orden")
    list_filter = ("incluido", "activo")


@admin.register(Huesped)
class HuespedAdmin(admin.ModelAdmin):
    list_display = ("nombre_completo", "email", "telefono", "creado_en")
    search_fields = ("nombre_completo", "email")


@admin.register(SolicitudReserva)
class SolicitudReservaAdmin(admin.ModelAdmin):
    list_display = (
        "huesped",
        "fecha_llegada",
        "fecha_salida",
        "noches",
        "personas",
        "casa_completa",
        "estado",
        "creada_en",
    )
    list_filter = ("estado", "casa_completa", "idioma")
    search_fields = ("huesped__nombre_completo", "huesped__email")
    date_hierarchy = "fecha_llegada"
    filter_horizontal = ("habitaciones",)

@admin.register(Resena)
class ResenaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "pais", "puntuacion", "aprobada", "creada")
    list_filter = ("aprobada", "puntuacion")
    actions = ["aprobar"]

    @admin.action(description="Aprobar reseñas seleccionadas")
    def aprobar(self, request, queryset):
        queryset.update(aprobada=True)