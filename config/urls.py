"""URL configuration for config project."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # Vista de Django para cambiar de idioma (recibe un POST con el idioma).
    path("i18n/", include("django.conf.urls.i18n")),
    path("", include("reservas.urls")),
]
