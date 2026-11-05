from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Huesped, SolicitudReserva


class OcupadasTests(TestCase):
    def test_solo_estadias_confirmadas_y_futuras(self):
        h = Huesped.objects.create(nombre_completo="Ana Pérez", email="ana@example.com")
        hoy = timezone.localdate()

        def crear(estado, desde, hasta):
            SolicitudReserva.objects.create(
                huesped=h, personas=2, estado=estado,
                fecha_llegada=hoy + timedelta(days=desde),
                fecha_salida=hoy + timedelta(days=hasta),
            )

        crear("confirmada", 5, 8)
        crear("pendiente", 10, 12)
        crear("rechazada", 15, 17)
        crear("confirmada", -10, -5)

        r = self.client.get(reverse("reservas:ocupadas"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(
            r.json()["ocupadas"],
            [[(hoy + timedelta(days=5)).isoformat(), (hoy + timedelta(days=8)).isoformat()]],
        )
        self.assertNotIn("ana", r.content.decode().lower())  # no se filtra ningún dato personal