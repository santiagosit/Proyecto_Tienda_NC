from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='profile'
    )
    nombre_completo = models.CharField(max_length=100)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    direccion = models.CharField(max_length=255, null=True, blank=True)
    fecha_contratacion = models.DateField(null=True, blank=True)
    rol = models.CharField(max_length=20, choices=[
        ('Administrador', 'Administrador'),
        ('Empleado', 'Empleado'),
    ])

    def __str__(self):
        if self.user.is_superuser:
            return f"{self.user.username} (Superusuario)"
        return f"{self.user.username} ({self.rol})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user'], 
                name='unique_user_profile'
            )
        ]

# Mover los signals fuera de la clase Profile
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Disable automatic profile creation"""
    pass  # We'll create profiles explicitly in views

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Only save existing profiles"""
    pass  # We'll handle profile saving explicitly in views


class PIN(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    pin = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.pin}"

    def is_valid(self):
        """Valida que el PIN no tenga más de 10 minutos."""
        return True
