from django.db import models
from django.utils import timezone
from app_inventario.models import Producto

class Proveedor(models.Model):
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15)
    email = models.EmailField(unique=True)
    direccion = models.TextField()
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Proveedor'
        verbose_name_plural = 'Proveedores'

class Pedido(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    fecha_pedido = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=[
        ('pedido', 'Pedido'),
        ('en camino', 'En camino'),
        ('recibido', 'Recibido'),
    ], default='pedido')

    @property
    def total(self):
        return sum(detalle.subtotal for detalle in self.detalles.all())

    def calcular_total(self):
        return self.total

    def __str__(self):
        return f'Pedido #{self.id} - {self.proveedor.nombre}'

class PedidoDetalle(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        return self.cantidad * self.costo_unitario

    def actualizar_stock(self):
        """Actualiza el stock del producto cuando el pedido se marca como recibido"""
        if self.pedido.estado == 'recibido':
            self.producto.cantidad_stock += self.cantidad
            self.producto.save()

    def __str__(self):
        return f"{self.producto.nombre} - {self.cantidad} unidades"




