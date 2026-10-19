from django.urls import path
 
from . import views
 
app_name = "reservas"
 
urlpatterns = [
    path("", views.solicitar_reserva, name="solicitar"),
    path("gracias/", views.gracias, name="gracias"),
]