import logging
from django.shortcuts import redirect
from django.urls import reverse, resolve
from app_usuarios.utils import is_admin_or_superuser, is_employee_or_above
from app_usuarios.models import Profile

logger = logging.getLogger(__name__)

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # URLs que requieren superusuario
        self.superuser_urls = [
            'crear_administrador',
            'listar_administradores',
            'editar_administrador',
            'eliminar_administrador',
        ]
        # URLs que requieren ser admin o superusuario
        self.admin_urls = [
            'crear_empleado',
            'listar_empleados',
            'editar_empleado',
            'eliminar_empleado',
            'registrar_producto',
            'eliminar_producto',
            'modificar_producto',
            'crear_evento',
            'editar_evento',
            'eliminar_evento',
        ]
        # URLs que requieren ser empleado o superior
        self.employee_urls = [
            'registrar_venta',
            'listar_ventas',
            'listar_productos',
            'listar_pedidos',
        ]

    def __call__(self, request):
        # Lista de nombres de vistas exentas
        exempt_views = [
            'login',  # Nombre de la URL que has definido en urls.py para el login
            'registrar_usuario',  # Nombre de la URL para registrar
            'recuperar_password',  # Nombre de la URL para recuperar contraseña
            'verificar_pin',  # Nombre de la URL para verificar el pin
            'enviar_pin',  # Nombre de la URL para enviar el pin
        ]

        # Obtener la vista que se está resolviendo
        resolver = resolve(request.path_info)
        view_name = resolver.url_name  # Nombre de la vista actual

        logger.debug(f"Request path: {request.path}")
        logger.debug(f"Exempt views: {exempt_views}")
        logger.debug(f"Current view name: {view_name}")

        # Si el usuario no está autenticado y la vista no está exenta, redirigir al login
        if not request.user.is_authenticated and view_name not in exempt_views:
            logger.debug("Redirecting to login")
            return redirect('login')

        # Add profile check
        if request.user.is_authenticated and not hasattr(request.user, 'profile'):
            Profile.objects.create(
                user=request.user,
                rol='Empleado' if not request.user.is_superuser else 'Administrador'
            )
            logger.info(f"Created missing profile for user {request.user.username}")

        # Verificar permisos específicos después de la autenticación
        if request.user.is_authenticated:
            resolver = resolve(request.path_info)
            view_name = resolver.url_name

            if view_name in self.superuser_urls and not request.user.is_superuser:
                logger.debug("Access denied: superuser required")
                return redirect('home')

            if view_name in self.admin_urls and not is_admin_or_superuser(request.user):
                logger.debug("Access denied: admin required")
                return redirect('home')

            if view_name in self.employee_urls and not is_employee_or_above(request.user):
                logger.debug("Access denied: employee access required")
                return redirect('home')

        # Continuar con el flujo de la aplicación
        response = self.get_response(request)
        return response
