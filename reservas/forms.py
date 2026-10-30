from django import forms
from django.db import transaction
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.utils import timezone
from .models import Habitacion, Huesped, SolicitudReserva, telefono_validator
from .models import Resena

# Clases de Tailwind para los campos del formulario (fondo oscuro del mockup).
CLASE_CAMPO = (
    "w-full border border-white/25 bg-bosque-700/70 px-4 py-3 text-sm text-beige-100 "
    "placeholder-beige-100/50 [color-scheme:dark] focus:border-terracota-600 "
    "focus:outline-none focus:ring-1 focus:ring-terracota-600"
)
CLASE_CASILLA = "h-4 w-4 accent-terracota-600"


class SolicitudReservaForm(forms.ModelForm):
    """Formulario público de solicitud de reserva (consulta de disponibilidad).

    Los datos del huésped se piden en el mismo formulario y se guardan en el
    modelo Huesped. Toda la validación ocurre en el servidor.
    """

    ALOJAMIENTO_CASA = "casa"
    ALOJAMIENTO_HABITACIONES = "habitaciones"

    nombre_completo = forms.CharField(label=_("Nombre de quien reserva"), max_length=120)
    email = forms.EmailField(label=_("Correo electrónico"))
    telefono = forms.CharField(
        label=_("Teléfono (opcional)"),
        max_length=20,
        required=False,
        validators=[telefono_validator],
    )
    alojamiento = forms.ChoiceField(
        label=_("Alojamiento"),
        choices=[
            (ALOJAMIENTO_CASA, _("Casa completa")),
            (ALOJAMIENTO_HABITACIONES, _("Habitaciones específicas")),
        ],
        initial=ALOJAMIENTO_CASA,
    )
    habitaciones_elegidas = forms.ModelMultipleChoiceField(
        label=_("¿Qué habitaciones?"),
        queryset=Habitacion.objects.none(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    field_order = [
        "nombre_completo",
        "email",
        "telefono",
        "fecha_llegada",
        "fecha_salida",
        "personas",
        "alojamiento",
        "habitaciones_elegidas",
        "comentarios",
        "contactar_por_whatsapp",
    ]

    class Meta:
        model = SolicitudReserva
        fields = [
            "fecha_llegada",
            "fecha_salida",
            "personas",
            "comentarios",
            "contactar_por_whatsapp",
        ]
        labels = {
            "fecha_llegada": _("Llegada"),
            "fecha_salida": _("Salida"),
            "personas": _("Número de personas"),
            "comentarios": _("¿Cómo podemos adaptar la estadía para ustedes?"),
            "contactar_por_whatsapp": _("Prefiero que me contacten por WhatsApp"),
        }
        widgets = {
            "fecha_llegada": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "fecha_salida": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "comentarios": forms.Textarea(attrs={"rows": 4, "maxlength": 1000}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["habitaciones_elegidas"].queryset = Habitacion.objects.filter(activa=True)
        self.fields["comentarios"].widget.attrs["placeholder"] = _(
            "Cuéntanos sobre tu grupo, alimentación o necesidades especiales…"
        )
        self.fields["personas"].widget.attrs["min"] = 1
        for campo in self.fields.values():
            if isinstance(campo.widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                campo.widget.attrs["class"] = CLASE_CASILLA
            else:
                campo.widget.attrs["class"] = CLASE_CAMPO
        # htmx: al cambiar una fecha, consulta la disponibilidad sin recargar.
        for nombre in ("fecha_llegada", "fecha_salida"):
            self.fields[nombre].widget.attrs.update({
                "hx-get": reverse("reservas:disponibilidad"),
                "hx-trigger": "change",
                "hx-target": "#aviso-fechas",
                "hx-indicator": "#aviso-fechas",
                "hx-include": "#id_fecha_llegada, #id_fecha_salida",
            })
        hoy = timezone.localdate().isoformat()
        for nombre in ("fecha_llegada", "fecha_salida"):
            self.fields[nombre].widget.attrs["min"] = hoy

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean(self):
        datos = super().clean()
        if (
            datos.get("alojamiento") == self.ALOJAMIENTO_HABITACIONES
            and not datos.get("habitaciones_elegidas")
        ):
            self.add_error(
                "habitaciones_elegidas",
                _("Elige al menos una habitación o selecciona la casa completa."),
            )
        if datos.get("contactar_por_whatsapp") and not datos.get("telefono"):
            self.add_error("telefono", _("Necesitamos tu teléfono para contactarte por WhatsApp."))
        llegada = datos.get("fecha_llegada")
        salida = datos.get("fecha_salida")
        if llegada and salida and salida > llegada:
            # Se recibe un solo grupo a la vez: no se aceptan fechas ya confirmadas.
            if SolicitudReserva.hay_conflicto(llegada, salida):
                self.add_error(
                    "fecha_llegada",
                    _("Esas fechas no están disponibles. Prueba con otras o escríbenos."),
                )   
        return datos

    def save(self):
        """Crea (o reutiliza por correo) al huésped y guarda la solicitud."""
        with transaction.atomic():
            # get_or_create: un visitante anónimo no puede modificar los datos
            # de un huésped que ya existe.
            huesped, _creado = Huesped.objects.get_or_create(
                email=self.cleaned_data["email"],
                defaults={
                    "nombre_completo": self.cleaned_data["nombre_completo"],
                    "telefono": self.cleaned_data["telefono"],
                },
            )
            solicitud = super().save(commit=False)
            solicitud.huesped = huesped
            solicitud.casa_completa = self.cleaned_data["alojamiento"] == self.ALOJAMIENTO_CASA
            solicitud.idioma = (translation.get_language() or "es")[:5]
            solicitud.save()
            if not solicitud.casa_completa:
                solicitud.habitaciones.set(self.cleaned_data["habitaciones_elegidas"])
        return solicitud

class ResenaForm(forms.ModelForm):
    # Campo trampa anti-spam: los humanos no lo ven, los bots sí lo llenan.
    sitio_web = forms.CharField(required=False, widget=forms.HiddenInput)

    puntuacion = forms.TypedChoiceField(
        choices=[(n, "★" * n) for n in range(5, 0, -1)],
        coerce=int,
        widget=forms.RadioSelect,
    )

    class Meta:
        model = Resena
        fields = ["nombre", "pais", "puntuacion", "comentario"]
        labels = {
            "nombre": _("Nombre"),
            "pais": _("País"),
            "comentario": _("Comentario"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre in ("nombre", "pais", "comentario"):
            self.fields[nombre].widget.attrs["class"] = CLASE_CAMPO
        self.fields["comentario"].widget.attrs["rows"] = 4