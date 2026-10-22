from datetime import timedelta

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Habitacion, Huesped, SolicitudReserva


class FormularioReservaTests(TestCase):
    def setUp(self):
        self.suite = Habitacion.objects.create(
            nombre="La Suite", tipo_bano="privado", capacidad_ideal=3
        )
        self.familiar_1 = Habitacion.objects.create(
            nombre="Habitación Familiar 1", tipo_bano="compartido", capacidad_ideal=3
        )
        self.url = reverse("reservas:solicitar")
        self.hoy = timezone.localdate()
        self.llegada = (self.hoy + timedelta(days=1)).isoformat()
        self.salida = (self.hoy + timedelta(days=3)).isoformat()

    def datos(self, **cambios):
        datos = {
            "nombre_completo": "Ana Prueba",
            "email": "Ana@Example.com",
            "telefono": "",
            "fecha_llegada": self.llegada,
            "fecha_salida": self.salida,
            "personas": 4,
            "alojamiento": "casa",
            "comentarios": "",
        }
        datos.update(cambios)
        return datos

    def test_get_muestra_el_formulario_con_token_csrf(self):
        respuesta = self.client.get(self.url)
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "csrfmiddlewaretoken")

    def test_casa_completa_se_guarda_y_redirige(self):
        respuesta = self.client.post(self.url, self.datos())
        self.assertRedirects(respuesta, reverse("reservas:gracias"))
        solicitud = SolicitudReserva.objects.get()
        self.assertTrue(solicitud.casa_completa)
        self.assertEqual(solicitud.habitaciones.count(), 0)
        self.assertEqual(Huesped.objects.get().email, "ana@example.com")

    def test_habitaciones_elegidas_se_guardan(self):
        datos = self.datos(
            alojamiento="habitaciones",
            habitaciones_elegidas=[self.suite.pk, self.familiar_1.pk],
        )
        self.client.post(self.url, datos)
        solicitud = SolicitudReserva.objects.get()
        self.assertFalse(solicitud.casa_completa)
        self.assertEqual(solicitud.habitaciones.count(), 2)

    def test_habitaciones_requiere_elegir_al_menos_una(self):
        respuesta = self.client.post(self.url, self.datos(alojamiento="habitaciones"))
        self.assertIn("habitaciones_elegidas", respuesta.context["form"].errors)
        self.assertEqual(SolicitudReserva.objects.count(), 0)

    def test_rechaza_fecha_pasada(self):
        ayer = (self.hoy - timedelta(days=1)).isoformat()
        respuesta = self.client.post(self.url, self.datos(fecha_llegada=ayer))
        self.assertIn("fecha_llegada", respuesta.context["form"].errors)
        self.assertEqual(SolicitudReserva.objects.count(), 0)

    def test_rechaza_salida_anterior_a_la_llegada(self):
        respuesta = self.client.post(self.url, self.datos(fecha_salida=self.llegada))
        self.assertIn("fecha_salida", respuesta.context["form"].errors)
        self.assertEqual(SolicitudReserva.objects.count(), 0)

    def test_whatsapp_exige_telefono(self):
        respuesta = self.client.post(self.url, self.datos(contactar_por_whatsapp="on"))
        self.assertIn("telefono", respuesta.context["form"].errors)
        con_telefono = self.datos(contactar_por_whatsapp="on", telefono="+56 9 1234 5678")
        self.assertRedirects(
            self.client.post(self.url, con_telefono), reverse("reservas:gracias")
        )

    def test_rechaza_fechas_ya_confirmadas(self):
        huesped = Huesped.objects.create(nombre_completo="Otro Grupo", email="otro@example.com")
        SolicitudReserva.objects.create(
            huesped=huesped,
            fecha_llegada=self.hoy + timedelta(days=2),
            fecha_salida=self.hoy + timedelta(days=5),
            personas=2,
            casa_completa=True,
            estado=SolicitudReserva.Estado.CONFIRMADA,
        )
        respuesta = self.client.post(self.url, self.datos())
        self.assertIn("fecha_llegada", respuesta.context["form"].errors)
        self.assertEqual(SolicitudReserva.objects.count(), 1)

    def test_rechaza_correo_invalido(self):
        respuesta = self.client.post(self.url, self.datos(email="no-es-un-correo"))
        self.assertIn("email", respuesta.context["form"].errors)
        self.assertEqual(Huesped.objects.count(), 0)

    def test_reutiliza_al_huesped_por_correo(self):
        self.client.post(self.url, self.datos())
        self.client.post(self.url, self.datos(email="ana@example.com", personas=2))
        self.assertEqual(Huesped.objects.count(), 1)
        self.assertEqual(SolicitudReserva.objects.count(), 2)

    def test_exige_token_csrf(self):
        cliente = Client(enforce_csrf_checks=True)
        respuesta = cliente.post(self.url, self.datos())
        self.assertEqual(respuesta.status_code, 403)
        self.assertEqual(SolicitudReserva.objects.count(), 0)

    def test_rechaza_metodos_no_permitidos(self):
        self.assertEqual(self.client.put(self.url).status_code, 405)


class DisponibilidadTests(TestCase):
    def setUp(self):
        self.url = reverse("reservas:disponibilidad")
        self.hoy = timezone.localdate()

    def consultar(self, llegada, salida):
        return self.client.get(
            self.url, {"fecha_llegada": llegada.isoformat(), "fecha_salida": salida.isoformat()}
        )

    def confirmar(self, llegada, salida, estado=SolicitudReserva.Estado.CONFIRMADA):
        huesped = Huesped.objects.create(nombre_completo="Otro Grupo", email="otro@example.com")
        SolicitudReserva.objects.create(
            huesped=huesped, fecha_llegada=llegada, fecha_salida=salida,
            personas=2, casa_completa=True, estado=estado,
        )

    def test_fechas_libres(self):
        respuesta = self.consultar(self.hoy + timedelta(days=10), self.hoy + timedelta(days=12))
        self.assertContains(respuesta, "Fechas disponibles")

    def test_fechas_ocupadas_por_reserva_confirmada(self):
        self.confirmar(self.hoy + timedelta(days=10), self.hoy + timedelta(days=14))
        respuesta = self.consultar(self.hoy + timedelta(days=12), self.hoy + timedelta(days=15))
        self.assertContains(respuesta, "ya están reservadas")

    def test_reserva_pendiente_no_bloquea(self):
        self.confirmar(
            self.hoy + timedelta(days=10), self.hoy + timedelta(days=14),
            estado=SolicitudReserva.Estado.PENDIENTE,
        )
        respuesta = self.consultar(self.hoy + timedelta(days=12), self.hoy + timedelta(days=15))
        self.assertContains(respuesta, "Fechas disponibles")

    def test_salida_debe_ser_posterior(self):
        dia = self.hoy + timedelta(days=10)
        self.assertContains(self.consultar(dia, dia), "posterior a la llegada")

    def test_fechas_incompletas_o_mal_formadas_no_muestran_nada(self):
        for datos in ({}, {"fecha_llegada": "2026-12-01"}, {"fecha_llegada": "x", "fecha_salida": "y"}):
            respuesta = self.client.get(self.url, datos)
            self.assertEqual(respuesta.status_code, 200)
            self.assertNotContains(respuesta, "<p")

    def test_solo_acepta_get(self):
        self.assertEqual(self.client.post(self.url).status_code, 405)

class IdiomasTests(TestCase):
    def pagina_en(self, idioma):
        self.client.post(reverse("set_language"), {"language": idioma, "next": "/"})
        return self.client.get(reverse("reservas:solicitar"))

    def test_español_por_defecto(self):
        self.assertContains(self.client.get(reverse("reservas:solicitar")), "Consultar disponibilidad")

    def test_cambia_a_ingles(self):
        self.assertContains(self.pagina_en("en"), "Check availability")

    def test_cambia_a_portugues(self):
        self.assertContains(self.pagina_en("pt"), "Consultar disponibilidade")        