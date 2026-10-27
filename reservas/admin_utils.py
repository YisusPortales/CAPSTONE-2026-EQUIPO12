from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html


class AccionesFilaMixin:
    """Agrega a cada fila de la lista una columna con botones Editar y Eliminar."""

    def get_list_display(self, request):
        return (*super().get_list_display(request), "acciones")

    @admin.display(description="Acciones")
    def acciones(self, obj):
        o = self.model._meta
        editar = reverse(f"admin:{o.app_label}_{o.model_name}_change", args=[obj.pk])
        borrar = reverse(f"admin:{o.app_label}_{o.model_name}_delete", args=[obj.pk])
        return format_html(
            '<a class="fila-boton" href="{}">Editar</a>'
            '<a class="fila-boton peligro" href="{}">Eliminar</a>',
            editar, borrar,
        )