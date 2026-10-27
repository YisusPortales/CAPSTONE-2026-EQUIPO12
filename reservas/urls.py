from django.urls import path

from . import views

app_name = "reservas"

urlpatterns = [
    path("", views.solicitar_reserva, name="solicitar"),
    path("gracias/", views.gracias, name="gracias"),
    path("disponibilidad/", views.disponibilidad, name="disponibilidad"),
    path("resenas/", views.resenas, name="resenas"),
    path("gestion/", views.gestion, name="gestion"),
    path("gestion/solicitudes/<int:pk>/<str:accion>/", views.gestion_solicitud, name="gestion_solicitud"),
    path("gestion/resenas/<int:pk>/<str:accion>/", views.gestion_resena, name="gestion_resena"),
    path("galeria/", views.galeria, name="galeria"),
]
