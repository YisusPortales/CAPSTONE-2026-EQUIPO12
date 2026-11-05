from datetime import date

from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings

from .models import Huesped, SolicitudReserva

E = SolicitudReserva.Estado


@override_settings(NOTIFY_EMAIL="admin@example.com", DEFAULT_FROM_EMAIL="hrp@example.com")
class CorreosTests(TestCase):
    def setUp(self):
        cache.clear()
        self.h = Huesped.objects.create(nombre_completo="Ana Pérez", email="ana@example.com")

    def crear(self, **kw):
        datos = dict(huesped=self.h, fecha_llegada=date(2027, 1, 10),
                     fecha_salida=date(2027, 1, 13), personas=2, idioma="es")
        datos.update(kw)
        with self.captureOnCommitCallbacks(execute=True):
            return SolicitudReserva.objects.create(**datos)

    def cambiar(self, s, estado):
        s.estado = estado
        with self.captureOnCommitCallbacks(execute=True):
            s.save(update_fields=["estado", "actualizada_en"])

    def test_solicitud_nueva_avisa_a_admin_y_cliente(self):
        self.crear()
        self.assertEqual(sorted(m.to[0] for m in mail.outbox), ["admin@example.com", "ana@example.com"])

    def test_acuse_en_el_idioma_del_cliente(self):
        self.crear(idioma="en")
        acuse = next(m for m in mail.outbox if m.to == ["ana@example.com"])
        self.assertIn("Hello", acuse.body)
        self.assertNotIn("Hola", acuse.body)

    def test_confirmar_y_rechazar_avisan_al_cliente(self):
        s = self.crear()
        mail.outbox.clear()
        self.cambiar(s, E.CONFIRMADA)
        self.assertEqual([m.to for m in mail.outbox], [["ana@example.com"]])
        mail.outbox.clear()
        self.cambiar(s, E.RECHAZADA)
        self.assertEqual([m.to for m in mail.outbox], [["ana@example.com"]])

    def test_volver_a_pendiente_o_guardar_sin_cambio_no_envia(self):
        s = self.crear()
        mail.outbox.clear()
        self.cambiar(s, E.PENDIENTE)
        self.assertEqual(len(mail.outbox), 0)

    def test_limite_de_acuses_por_correo(self):
        for _ in range(5):
            self.crear()
        acuses = [m for m in mail.outbox if m.to == ["ana@example.com"]]
        self.assertEqual(len(acuses), 3)

    def test_fallo_del_smtp_no_rompe(self):
        from unittest import mock
        with mock.patch("reservas.correos.EmailMessage.send", side_effect=OSError("smtp caido")):
            self.crear()  # no debe lanzar excepción

    def test_usa_el_nombre_de_cada_solicitud(self):
        self.crear(nombre_contacto="Beto Soto")
        acuse = next(m for m in mail.outbox if m.to == ["ana@example.com"])
        self.assertIn("Beto Soto", acuse.body)
        self.assertNotIn("Ana Pérez", acuse.body)