from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from . import correos
from .models import SolicitudReserva

E = SolicitudReserva.Estado


@receiver(pre_save, sender=SolicitudReserva)
def recordar_estado(sender, instance, raw=False, **kwargs):
    instance._estado_previo = None
    if instance.pk and not raw:
        instance._estado_previo = (
            sender.objects.filter(pk=instance.pk).values_list("estado", flat=True).first()
        )


@receiver(post_save, sender=SolicitudReserva)
def avisar(sender, instance, created, raw=False, **kwargs):
    if raw:
        return
    if created:
        transaction.on_commit(lambda: correos.nueva_solicitud(instance))
    elif instance._estado_previo != instance.estado and instance.estado in (E.CONFIRMADA, E.RECHAZADA):
        transaction.on_commit(lambda: correos.estado_cambiado(instance))