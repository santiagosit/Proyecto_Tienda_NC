from django.db import models

class Cliente(models.Model):
    """Modelo de Cliente con datos adicionales."""
    nombre = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} - {self.telefono}"


class Evento(models.Model):
    """Modelo de Reserva con datos adicionales."""
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    descripcion = models.TextField()
    fecha_evento = models.DateTimeField()
    estado = models.CharField(max_length=20, choices=[
        ('Pendiente', 'Pendiente'),
        ('Confirmado', 'Confirmado'),
        ('Cancelado', 'Cancelado'),
    ], default='Pendiente')

    def __str__(self):
        return f"Evento de {self.cliente.nombre} - {self.fecha_evento}"
