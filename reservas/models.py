import uuid
import re
from urllib.parse import parse_qs, urlparse
from pathlib import Path
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db.models.signals import post_delete
from django.dispatch import receiver
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

def ruta_foto(instance, filename):
    """Guarda cada foto con un nombre aleatorio, nunca con el nombre original."""
    return f"galeria/{uuid.uuid4().hex}{Path(filename).suffix.lower()}"


def ruta_video(instance, filename):
    return f"videos/{uuid.uuid4().hex}{Path(filename).suffix.lower()}"


def validar_peso(archivo):
    if archivo.size > 8 * 1024 * 1024:
        raise ValidationError(_("La imagen no puede pesar más de 8 MB."))


def validar_peso_video(archivo):
    if archivo.size > 50 * 1024 * 1024:
        raise ValidationError(_("El video no puede pesar más de 50 MB."))


def validar_cabecera_video(archivo):
    """Comprueba que el contenido sea realmente MP4 o WebM, sin fiarse solo de la extensión."""
    if getattr(archivo, "_committed", False):
        return  # archivo ya guardado antes, no se vuelve a revisar
    cabecera = archivo.read(12)
    archivo.seek(0)
    es_mp4 = cabecera[4:8] == b"ftyp"
    es_webm = cabecera[:4] == b"\x1a\x45\xdf\xa3"
    if not (es_mp4 or es_webm):
        raise ValidationError(_("El archivo no es un video MP4 o WebM válido."))


def datos_de_enlace(enlace):
    """
    Devuelve (proveedor, url_para_incrustar, es_vertical) si el enlace es de un sitio
    permitido, o None. La URL de incrustación se arma aquí, nunca se copia del enlace.
    """
    u = urlparse((enlace or "").strip())
    if u.scheme != "https":
        return None
    host = (u.hostname or "").lower().removeprefix("www.")

    if host in ("youtube.com", "m.youtube.com", "youtu.be"):
        codigo = None
        if host == "youtu.be":
            m = re.fullmatch(r"/([\w-]{11})", u.path)
            codigo = m.group(1) if m else None
        elif u.path == "/watch":
            valor = parse_qs(u.query).get("v", [""])[0]
            codigo = valor if re.fullmatch(r"[\w-]{11}", valor) else None
        else:
            m = re.fullmatch(r"/(?:shorts|embed)/([\w-]{11})", u.path)
            codigo = m.group(1) if m else None
            if codigo and u.path.startswith("/shorts/"):
                return ("youtube", f"https://www.youtube-nocookie.com/embed/{codigo}", True)
        if codigo:
            return ("youtube", f"https://www.youtube-nocookie.com/embed/{codigo}", False)

    if host == "vimeo.com":
        m = re.fullmatch(r"/(\d{6,12})/?", u.path)
        if m:
            return ("vimeo", f"https://player.vimeo.com/video/{m.group(1)}", False)

    if host == "instagram.com":
        m = re.fullmatch(r"/(p|reel|tv)/([\w-]{5,30})/?", u.path)
        if m:
            return ("instagram", f"https://www.instagram.com/{m.group(1)}/{m.group(2)}/embed", True)

    return None


class CategoriaFoto(models.TextChoices):
    EXTERIORES = "exteriores", _("Exteriores")
    FAMILIAS = "familias", _("Familias")
    COMIDAS = "comidas", _("Comidas y bebidas")
    HABITACIONES = "habitaciones", _("Habitaciones")


class Foto(models.Model):
    imagen = models.ImageField(
        _("imagen"),
        upload_to=ruta_foto,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"]), validar_peso],
        help_text=_("JPG, PNG o WebP, hasta 8 MB."),
    )
    descripcion = models.CharField(
        _("descripción"), max_length=140, blank=True,
        help_text=_("Opcional. Describe la foto para personas con lectores de pantalla."),
    )
    categoria = models.CharField(
        _("categoría"), max_length=20, choices=CategoriaFoto.choices, blank=True,
        help_text=_("Si la dejas vacía, la foto solo aparece en «Todas»."),
    )
    orden = models.PositiveSmallIntegerField(_("orden"), default=0, help_text=_("Menor número, aparece antes."))
    activa = models.BooleanField(_("visible"), default=True)
    creada = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["orden", "-creada"]
        verbose_name = _("foto")
        verbose_name_plural = _("fotos")

    def __str__(self):
        return self.descripcion or f"Foto {self.pk}"


class Video(models.Model):
    titulo = models.CharField(_("título"), max_length=140, blank=True)
    archivo = models.FileField(
        _("archivo de video"), upload_to=ruta_video, blank=True,
        validators=[FileExtensionValidator(["mp4", "webm"]), validar_peso_video, validar_cabecera_video],
        help_text=_("MP4 o WebM, hasta 50 MB."),
    )
    enlace = models.URLField(
        _("enlace"), blank=True,
        help_text=_("YouTube, Vimeo o una publicación/reel público de Instagram."),
    )
    portada = models.ImageField(
        _("portada"), upload_to=ruta_foto, blank=True,
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"]), validar_peso],
        help_text=_("Opcional. Imagen que se ve antes de reproducir."),
    )
    orden = models.PositiveSmallIntegerField(_("orden"), default=0)
    activo = models.BooleanField(_("visible"), default=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["orden", "-creado"]
        verbose_name = _("video")
        verbose_name_plural = _("videos")

    def __str__(self):
        return self.titulo or self.enlace or f"Video {self.pk}"

    def clean(self):
        if bool(self.archivo) == bool(self.enlace):
            raise ValidationError(_("Sube un archivo o pega un enlace, pero no ambos."))
        if self.enlace and not datos_de_enlace(self.enlace):
            raise ValidationError({"enlace": _(
                "Solo se aceptan enlaces https de YouTube, Vimeo o Instagram (publicación o reel)."
            )})

    @property
    def _datos(self):
        return datos_de_enlace(self.enlace) if self.enlace else None

    @property
    def proveedor(self):
        return self._datos[0] if self._datos else ""

    @property
    def embed_url(self):
        return self._datos[1] if self._datos else ""

    @property
    def es_vertical(self):
        return bool(self._datos and self._datos[2])


@receiver(post_delete, sender=Foto)
def borrar_archivo_de_foto(sender, instance, **kwargs):
    instance.imagen.delete(save=False)


@receiver(post_delete, sender=Video)
def borrar_archivos_de_video(sender, instance, **kwargs):
    instance.archivo.delete(save=False)
    instance.portada.delete(save=False)