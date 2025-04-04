from django.db import models
from app_inventario.models import Producto


class Venta(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='ventas_reportes')
    cantidad = models.IntegerField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField()
    hora = models.TimeField()
    observaciones = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.producto.nombre} - {self.cantidad}'
