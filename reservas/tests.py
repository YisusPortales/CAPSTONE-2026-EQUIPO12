from django.test import TestCase
from datetime import timedelta
 
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
 
from .models import Habitacion, Huesped, SolicitudReserva
 
 
class SolicitudReservaTests(TestCase):
    def setUp(self):
        self.habitacion = Habitacion.objects.create(
            nombre="Suite Picunche", tipo_bano="privado", capacidad_max=3
        )
        self.huesped = Huesped.objects.create(nombre_completo="Ana Prueba", email="ana@example.com")
        self.manana = timezone.localdate() + timedelta(days=1)
 
    def nueva(self, **cambios):
        datos = dict(
            huesped=self.huesped,
            habitacion=self.habitacion,
            fecha_llegada=self.manana,
            noches=2,
            personas=2,
        )
        datos.update(cambios)
        return SolicitudReserva(**datos)
 
    def test_solicitud_valida_queda_pendiente(self):
        solicitud = self.nueva()
        solicitud.full_clean()
        solicitud.save()
        self.assertEqual(solicitud.estado, SolicitudReserva.Estado.PENDIENTE)
 
    def test_rechaza_fecha_pasada(self):
        solicitud = self.nueva(fecha_llegada=timezone.localdate() - timedelta(days=1))
        with self.assertRaises(ValidationError):
            solicitud.full_clean()
 
    def test_rechaza_noches_cero(self):
        with self.assertRaises(ValidationError):
            self.nueva(noches=0).full_clean()
 
    def test_rechaza_mas_personas_que_la_capacidad(self):
        with self.assertRaises(ValidationError):
            self.nueva(personas=4).full_clean()
 
    def test_base_de_datos_rechaza_noches_cero(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                self.nueva(noches=0).save()
 
    def test_email_del_huesped_es_unico(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Huesped.objects.create(nombre_completo="Otra Persona", email="ana@example.com")
 