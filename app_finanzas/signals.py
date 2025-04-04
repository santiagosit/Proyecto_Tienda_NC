from django.db.models.signals import post_save
from django.dispatch import receiver
from app_ventas.models import Venta
from app_pedidos.models import Pedido
from .models import Ingreso, Egreso
from django.db import transaction

@receiver(post_save, sender=Venta)
def crear_ingreso_por_venta(sender, instance, created, **kwargs):
    if created:
        Ingreso.objects.create(
            venta=instance,
            monto=instance.total,
            descripcion=f'Ingreso por Venta ID {instance.id}'
        )

@receiver(post_save, sender=Pedido)
def crear_egreso_por_pedido(sender, instance, created, **kwargs):
    if not created and instance.estado == 'recibido':
        # Verificar si ya existe un egreso para este pedido
        if not Egreso.objects.filter(pedido=instance).exists():
            Egreso.objects.create(
                pedido=instance,
                monto=instance.total,
                fecha=instance.fecha_pedido,
                tipo='pedido'
            )
