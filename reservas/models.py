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
 
telefono_validator = RegexValidator(
    r"^\+?[0-9 ()-]{7,20}$", _("Ingresa un teléfono válido.")
)
 
 
class Habitacion(models.Model):
    class TipoBano(models.TextChoices):
        PRIVADO = "privado", _("Baño privado")
        COMPARTIDO = "compartido", _("Baño compartido")
 
    nombre = models.CharField(max_length=80, unique=True)
    tipo_bano = models.CharField(max_length=12, choices=TipoBano.choices)
    capacidad_max = models.PositiveSmallIntegerField(validators=[MinValueValidator(1)])
    activa = models.BooleanField(default=True)
 
    class Meta:
        verbose_name = _("habitación")
        verbose_name_plural = _("habitaciones")
        ordering = ["nombre"]
 
    def __str__(self):
        return self.nombre
 
 
class Servicio(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    incluido = models.BooleanField(
        default=True, help_text=_("Incluido en la tarifa (si no, tiene costo adicional).")
    )
    activo = models.BooleanField(default=True)
 
    class Meta:
        ordering = ["nombre"]
 
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
    habitacion = models.ForeignKey(
        Habitacion,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="solicitudes",
        help_text=_("Vacío significa sin preferencia."),
    )
    fecha_llegada = models.DateField()
    noches = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(30)]
    )
    personas = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    comentarios = models.TextField(blank=True, validators=[MaxLengthValidator(1000)])
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
                condition=models.Q(noches__gte=1, noches__lte=30), name="noches_entre_1_y_30"
            ),
            models.CheckConstraint(condition=models.Q(personas__gte=1), name="personas_minimo_1"),
        ]
 
    def clean(self):
        errores = {}
        if self.fecha_llegada and self.fecha_llegada < timezone.localdate():
            errores["fecha_llegada"] = _("La fecha de llegada no puede ser pasada.")
        if self.habitacion_id and self.personas and self.personas > self.habitacion.capacidad_max:
            errores["personas"] = _("La habitación elegida no admite tantas personas.")
        if errores:
            raise ValidationError(errores)
 
    def __str__(self):
        return f"{self.huesped.nombre_completo} - {self.fecha_llegada} ({self.estado})"
 