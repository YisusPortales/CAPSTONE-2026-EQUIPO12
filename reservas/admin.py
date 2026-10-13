from django.contrib import admin
 
from .models import Habitacion, Huesped, Servicio, SolicitudReserva
 
 
@admin.register(Habitacion)
class HabitacionAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo_bano", "capacidad_max", "activa")
    list_filter = ("tipo_bano", "activa")
 
 
@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ("nombre", "incluido", "activo")
    list_filter = ("incluido", "activo")
 
 
@admin.register(Huesped)
class HuespedAdmin(admin.ModelAdmin):
    list_display = ("nombre_completo", "email", "telefono", "creado_en")
    search_fields = ("nombre_completo", "email")
 
 
@admin.register(SolicitudReserva)
class SolicitudReservaAdmin(admin.ModelAdmin):
    list_display = ("huesped", "habitacion", "fecha_llegada", "noches", "personas", "estado", "creada_en")
    list_filter = ("estado", "habitacion", "idioma")
    search_fields = ("huesped__nombre_completo", "huesped__email")
    date_hierarchy = "fecha_llegada"
 