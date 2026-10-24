from django.core.exceptions import ValidationError
from django.core.validators import (
    MaxLengthValidator,
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Q

telefono_validator = RegexValidator(
    r"^\+?[0-9 ()-]{7,20}$", _("Ingresa un teléfono válido.")
)

# Límites técnicos, no reglas del negocio: el hospedaje no define un máximo de
# personas ni de noches, pero se evitan valores absurdos o abusivos.
MAX_PERSONAS = 100
MAX_NOCHES = 365


class Habitacion(models.Model):
    class TipoBano(models.TextChoices):
        PRIVADO = "privado", _("Baño privado")
        COMPARTIDO = "compartido", _("Baño compartido")

    nombre = models.CharField(max_length=80, unique=True)
    tipo_bano = models.CharField(max_length=12, choices=TipoBano.choices)
    capacidad_ideal = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1)],
        help_text=_("Referencial: se pueden sumar camas según el grupo."),
    )
    activa = models.BooleanField(default=True)
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        verbose_name = _("habitación")
        verbose_name_plural = _("habitaciones")
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class Servicio(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    incluido = models.BooleanField(
        default=True, help_text=_("Incluido en la estadía (si no, es adicional).")
    )
    activo = models.BooleanField(
        default=True, help_text=_("Desmarcar si aún no está habilitado (próximamente).")
    )
    orden = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["orden", "nombre"]

    def __str__(self):
        return self.nombre


class Huesped(models.Model):
    nombre_completo = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True, validators=[telefono_validator])
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("huésped")
        verbose_name_plural = _("huéspedes")

    def __str__(self):
        return f"{self.nombre_completo} <{self.email}>"


class SolicitudReserva(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", _("Pendiente")
        CONFIRMADA = "confirmada", _("Confirmada")
        RECHAZADA = "rechazada", _("Rechazada")

    huesped = models.ForeignKey(Huesped, on_delete=models.PROTECT, related_name="solicitudes")
    fecha_llegada = models.DateField()
    fecha_salida = models.DateField()
    personas = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(MAX_PERSONAS)]
    )
    casa_completa = models.BooleanField(default=False)
    habitaciones = models.ManyToManyField(Habitacion, blank=True, related_name="solicitudes")
    comentarios = models.TextField(blank=True, validators=[MaxLengthValidator(1000)])
    contactar_por_whatsapp = models.BooleanField(default=False)
    idioma = models.CharField(max_length=5, default="es")
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.PENDIENTE)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("solicitud de reserva")
        verbose_name_plural = _("solicitudes de reserva")
        ordering = ["-creada_en"]
        constraints = [
            # Reglas también a nivel de base de datos (Django 5.1 o superior).
            models.CheckConstraint(
                condition=models.Q(fecha_salida__gt=models.F("fecha_llegada")),
                name="salida_posterior_a_llegada",
            ),
            models.CheckConstraint(
                condition=models.Q(personas__gte=1, personas__lte=MAX_PERSONAS),
                name="personas_dentro_del_limite",
            ),
        ]

    @property
    def noches(self):
        if self.fecha_llegada and self.fecha_salida:
            return (self.fecha_salida - self.fecha_llegada).days
        return None

    @classmethod
    def hay_conflicto(cls, llegada, salida, excluir_pk=None):
        """Regla de negocio: se recibe un solo grupo a la vez.

        Hay conflicto si alguna estadía CONFIRMADA se cruza con las fechas
        dadas. Salir un día y llegar otro grupo el mismo día no es conflicto.
        """
        cruces = cls.objects.filter(
            estado=cls.Estado.CONFIRMADA,
            fecha_llegada__lt=salida,
            fecha_salida__gt=llegada,
        )
        if excluir_pk:
            cruces = cruces.exclude(pk=excluir_pk)
        return cruces.exists()

    def clean(self):
        errores = {}
        if self.fecha_llegada and self._state.adding and self.fecha_llegada < timezone.localdate():
            errores["fecha_llegada"] = _("La fecha de llegada no puede ser pasada.")
        if self.fecha_llegada and self.fecha_salida:
            if self.fecha_salida <= self.fecha_llegada:
                errores["fecha_salida"] = _("La salida debe ser posterior a la llegada.")
            elif self.noches > MAX_NOCHES:
                errores["fecha_salida"] = _(
                    "La estadía es muy larga; escríbenos para coordinarla."
                )
            elif (
                self.estado == self.Estado.CONFIRMADA
                and "fecha_llegada" not in errores
                and self.hay_conflicto(self.fecha_llegada, self.fecha_salida, self.pk)
            ):
                errores["fecha_llegada"] = _("Ya hay una estadía confirmada en esas fechas.")
        if errores:
            raise ValidationError(errores)

    def __str__(self):
        return f"{self.huesped.nombre_completo} - {self.fecha_llegada} ({self.estado})"

class Resena(models.Model):
    nombre = models.CharField(max_length=80)
    pais = models.CharField(max_length=60, blank=True)
    puntuacion = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comentario = models.TextField(max_length=600)
    creada = models.DateTimeField(auto_now_add=True)
    aprobada = models.BooleanField(default=False)

    class Meta:
        ordering = ["-creada"]
        constraints = [
            models.CheckConstraint(
                condition=Q(puntuacion__gte=1, puntuacion__lte=5),
                name="resena_puntuacion_1_a_5",
            )
        ]

    @property
    def estrellas(self):
        return "★" * self.puntuacion + "☆" * (5 - self.puntuacion)

    def __str__(self):
        return f"{self.nombre} ({self.puntuacion}/5)"