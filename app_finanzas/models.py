from django.db import models
from django.core.validators import DecimalValidator
from decimal import Decimal
from app_ventas.models import Venta
from app_pedidos.models import Pedido

class Ingreso(models.Model):
    TIPO_CHOICES = [
        ('venta', 'Venta'),
        ('personalizado', 'Personalizado'),
    ]
    
    venta = models.OneToOneField('app_ventas.Venta', on_delete=models.CASCADE, null=True, blank=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField(blank=True, null=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='venta')

    class Meta:
        ordering = ['-fecha']

    @property
    def subtotal(self):
        """Calcular el subtotal basado en el tipo de ingreso"""
        return self.monto

    def __str__(self):
        if self.venta:
            return f'Ingreso de Venta #{self.venta.id} - ${self.monto}'
        return f'Ingreso Personalizado - ${self.monto}'

# app_finanzas/models.py
class Egreso(models.Model):
    TIPO_CHOICES = [
        ('pedido', 'Pedido'),
        ('personalizado', 'Personalizado')
    ]
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES, default='pedido')
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name='egreso', null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=100, default='Pedido')  # Categoría personalizada

    def __str__(self):
        return f'Egreso - {self.tipo.capitalize()} - {self.monto}'

