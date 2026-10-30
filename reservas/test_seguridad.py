from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class GestionAccesoTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.normal = User.objects.create_user("visita", password="Clave-Segura-123")
        self.personal = User.objects.create_user("equipo", password="Clave-Segura-123", is_staff=True)

    def test_anonimo_recibe_404(self):
        self.assertEqual(self.client.get(reverse("reservas:gestion")).status_code, 404)

    def test_usuario_sin_permiso_recibe_404(self):
        self.client.force_login(self.normal)
        self.assertEqual(self.client.get(reverse("reservas:gestion")).status_code, 404)

    def test_personal_entra(self):
        self.client.force_login(self.personal)
        self.assertEqual(self.client.get(reverse("reservas:gestion")).status_code, 200)


class BloqueoDeLoginTests(TestCase):
    def test_muchos_intentos_fallidos_bloquean(self):
        url = reverse("admin:login")
        for _ in range(10):
            respuesta = self.client.post(url, {"username": "atacante", "password": "mala"})
        self.assertEqual(respuesta.status_code, 429)