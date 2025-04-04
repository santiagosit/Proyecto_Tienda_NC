from django.db import models
from django.shortcuts import render


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad_stock = models.IntegerField()
    stock_minimo = models.IntegerField(default=3)  # Stock mínimo definido.

    def __str__(self):
        return self.nombre

    def stock_bajo(self):
        return self.cantidad_stock < self.stock_minimo
