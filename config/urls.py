"""URL configuration for config project."""

from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    # Vista de Django para cambiar de idioma (recibe un POST con el idioma).
    path("i18n/", include("django.conf.urls.i18n")),
    path("", include("reservas.urls")),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)