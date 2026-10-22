from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from .models import Habitacion, Huesped, SolicitudReserva


class SolicitudReservaTests(TestCase):
    def setUp(self):
        self.huesped = Huesped.objects.create(nombre_completo="Ana Prueba", email="ana@example.com")
        self.hoy = timezone.localdate()
        self.manana = self.hoy + timedelta(days=1)

    def nueva(self, **cambios):
        datos = dict(
            huesped=self.huesped,
            fecha_llegada=self.manana,
            fecha_salida=self.manana + timedelta(days=2),
            personas=2,
            casa_completa=True,
        )
        datos.update(cambios)
        return SolicitudReserva(**datos)

    def test_solicitud_valida_queda_pendiente(self):
        solicitud = self.nueva()
        solicitud.full_clean()
        solicitud.save()
        self.assertEqual(solicitud.estado, SolicitudReserva.Estado.PENDIENTE)

    def test_las_noches_se_calculan(self):
        self.assertEqual(self.nueva().noches, 2)

    def test_rechaza_fecha_pasada(self):
        solicitud = self.nueva(
            fecha_llegada=self.hoy - timedelta(days=1), fecha_salida=self.manana
        )
        with self.assertRaises(ValidationError):
            solicitud.full_clean()

    def test_rechaza_salida_igual_o_anterior_a_la_llegada(self):
        for salida in (self.manana, self.manana - timedelta(days=1)):
            with self.assertRaises(ValidationError):
                self.nueva(fecha_salida=salida).full_clean()

    def test_rechaza_estadias_demasiado_largas(self):
        solicitud = self.nueva(fecha_salida=self.manana + timedelta(days=366))
        with self.assertRaises(ValidationError):
            solicitud.full_clean()

    def test_no_hay_maximo_practico_de_personas(self):
        solicitud = self.nueva(personas=40)
        solicitud.full_clean()

    def test_base_de_datos_rechaza_salida_anterior_a_llegada(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.nueva(fecha_salida=self.manana - timedelta(days=1)).save()

    def test_email_del_huesped_es_unico(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Huesped.objects.create(nombre_completo="Otra Persona", email="ana@example.com")

    def test_un_solo_grupo_a_la_vez(self):
        self.nueva(estado=SolicitudReserva.Estado.CONFIRMADA).save()
        cruzada = self.nueva(
            estado=SolicitudReserva.Estado.CONFIRMADA,
            fecha_llegada=self.manana + timedelta(days=1),
            fecha_salida=self.manana + timedelta(days=3),
        )
        with self.assertRaises(ValidationError):
            cruzada.full_clean()

    def test_se_puede_llegar_el_dia_que_otro_grupo_sale(self):
        self.nueva(estado=SolicitudReserva.Estado.CONFIRMADA).save()
        seguida = self.nueva(
            estado=SolicitudReserva.Estado.CONFIRMADA,
            fecha_llegada=self.manana + timedelta(days=2),
            fecha_salida=self.manana + timedelta(days=4),
        )
        seguida.full_clean()

    def test_una_solicitud_pendiente_puede_cruzarse(self):
        self.nueva(estado=SolicitudReserva.Estado.CONFIRMADA).save()
        pendiente = self.nueva()
        pendiente.full_clean()
