from django.shortcuts import redirect
from functools import wraps
from .models import Profile

def is_admin_or_superuser(user):
    """Verifica si el usuario es admin o superusuario"""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        profile = Profile.objects.get(user=user)
        return profile.rol == 'Administrador'
    except Profile.DoesNotExist:
        return False

def is_employee_or_above(user):
    """Verifica si el usuario es empleado, admin o superusuario"""
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    try:
        profile = Profile.objects.get(user=user)
        return profile.rol in ['Administrador', 'Empleado']
    except Profile.DoesNotExist:
        return False

def is_employee(user):
    """Verifica si el usuario es empleado"""
    if not user.is_authenticated:
        return False
    try:
        profile = Profile.objects.get(user=user)
        return profile.rol == 'Empleado'
    except Profile.DoesNotExist:
        return False

def employee_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if is_employee(request.user):
            return function(request, *args, **kwargs)
        return redirect('home')
    return wrap