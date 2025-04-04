from django.db import models
from django.db.models import Sum, F
from decimal import Decimal
from app_inventario.models import Producto
from app_usuarios.models import Profile

class Venta(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    
    empleado = models.ForeignKey(Profile, on_delete=models.PROTECT)
    creado_por = models.ForeignKey(
        Profile, 
        on_delete=models.PROTECT, 
        related_name='ventas_creadas',
        null=True  # Temporarily allow null
    )
    modificado_por = models.ForeignKey(
        Profile, 
        on_delete=models.PROTECT, 
        related_name='ventas_modificadas', 
        null=True,
        blank=True
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observaciones = models.TextField(blank=True, null=True)

    def actualizar_total(self):
        """Actualiza el total de la venta basado en sus detalles"""
        self.total = sum(detalle.precio_total for detalle in self.detalles.all())
        self.save()

    def completar_venta(self):
        """Completa la venta y crea el registro de ingreso"""
        if self.estado == 'pendiente':
            self.actualizar_total()
            self.estado = 'completada'
            self.save()
            
            # Crear ingreso solo si no existe
            from app_finanzas.models import Ingreso
            if not hasattr(self, 'ingreso'):
                Ingreso.objects.create(
                    venta=self,
                    monto=self.total,
                    subtotal=self.total,
                    iva=Decimal('0.00'),
                    descripcion=f'Ingreso por venta #{self.id}'
                )

    def actualizar_stock(self, detalle, cantidad_anterior):
        """Actualiza el stock del producto basado en el cambio de cantidad"""
        diferencia = detalle.cantidad - cantidad_anterior
        if diferencia != 0:
            producto = detalle.producto
            if diferencia > 0:  # Se aumentó la cantidad
                if producto.cantidad_stock >= diferencia:
                    producto.cantidad_stock -= diferencia
                    producto.save()
                else:
                    raise ValueError(f'Stock insuficiente para {producto.nombre}')
            else:  # Se disminuyó la cantidad
                producto.cantidad_stock += abs(diferencia)
                producto.save()

    @property
    def subtotal(self):
        """Calcula el subtotal de la venta (sin IVA)"""
        return self.total / Decimal('1.19')  # Asumiendo IVA del 19%

    @property
    def iva(self):
        """Calcula el IVA de la venta"""
        return self.total - self.subtotal

    def __str__(self):
        return f'Venta #{self.id} - {self.estado}'

class VentaDetalle(models.Model):
    venta = models.ForeignKey(Venta, related_name='detalles', on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    precio_total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.pk:  # Nuevo detalle
            if self.producto.cantidad_stock < self.cantidad:
                raise ValueError(f'Stock insuficiente para {self.producto.nombre}')
            self.producto.cantidad_stock -= self.cantidad  # Primera reducción
            self.producto.save()
        else:  # Detalle existente
            original = VentaDetalle.objects.get(pk=self.pk)
            if self.cantidad != original.cantidad:
                self.venta.actualizar_stock(self, original.cantidad)

        # Calcular precio total
        self.precio_unitario = Decimal(str(self.precio_unitario))
        self.precio_total = self.precio_unitario * Decimal(str(self.cantidad))
        
        super().save(*args, **kwargs)
        self.venta.actualizar_total()

    def delete(self, *args, **kwargs):
        """Restaura el stock al eliminar un detalle"""
        self.producto.cantidad_stock += self.cantidad
        self.producto.save()
        super().delete(*args, **kwargs)
        self.venta.actualizar_total()

    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}'
