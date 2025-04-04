# Importaciones de Python
from pyexpat.errors import messages
import random

# Importaciones de Django
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import transaction, IntegrityError  # Add IntegrityError here
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.urls import reverse
from django.contrib import messages
from django.db.models import Sum, F, Count  # Change this import
from decimal import Decimal

# Importaciones locales
from ProyectoWeb import settings
from app_finanzas.models import Egreso, Ingreso
from app_inventario.models import Producto
from app_pedidos.models import Pedido
from app_ventas.models import Venta, VentaDetalle  # Añadir VentaDetalle
from .forms import UserForm, ProfileForm
from .models import Profile, PIN
from .utils import is_admin_or_superuser, is_employee_or_above, employee_required
from app_eventos.models import Evento

# Vistas de autenticación
def login_view(request):
    """Vista para mostrar el formulario de inicio de sesión"""
    return render(request, 'usuarios/login.html')

def iniciar_sesion(request):
    """Vista para procesar el inicio de sesión"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if hasattr(user, 'profile'):
                if user.profile.rol == 'Empleado':
                    return redirect('empleado_dashboard')
                elif user.profile.rol == 'Administrador' or user.is_superuser:
                    return redirect('home')
            messages.error(request, 'Usuario sin perfil asignado')
        else:
            messages.error(request, 'Credenciales incorrectas')
        return render(request, 'usuarios/login.html')
    return render(request, 'usuarios/login.html')

def logout_view(request):
    """Vista para cerrar sesión"""
    logout(request)
    return redirect('login')

@login_required
def home(request):
    # Quitar el espacio extra después de 'Empleado'
    if request.user.profile.rol == 'Empleado':
        return redirect('empleado_dashboard')
    today = timezone.now()
    start_of_month = today.replace(day=1)

    # Estadísticas financieras
    ingresos_hoy = Ingreso.objects.filter(fecha__date=today.date()).aggregate(total=Sum('monto'))['total'] or 0
    egresos_hoy = Egreso.objects.filter(fecha__date=today.date()).aggregate(total=Sum('monto'))['total'] or 0
    ingresos_mes = Ingreso.objects.filter(fecha__gte=start_of_month).aggregate(total=Sum('monto'))['total'] or 0
    egresos_mes = Egreso.objects.filter(fecha__gte=start_of_month).aggregate(total=Sum('monto'))['total'] or 0
    balance_mes = ingresos_mes - egresos_mes

    # Ventas
    ventas_hoy = Venta.objects.filter(fecha_creacion__date=today.date()).count()
    ultimas_ventas = Venta.objects.all().order_by('-fecha_creacion')[:5]

    # Eventos
    eventos_pendientes_count = Evento.objects.filter(estado='Pendiente').count()
    eventos_proximos = Evento.objects.filter(fecha_evento__gte=today).order_by('fecha_evento')[:5]

    # Inventario
    productos_sin_stock_count = Producto.objects.filter(stock=0).count()
    productos_bajo_stock_count = Producto.objects.filter(stock__lte=10, stock__gt=0).count()
    productos_stock_normal_count = Producto.objects.filter(stock__gt=10).count()

    # Pedidos
    pedidos_pendientes = Pedido.objects.filter(estado='Pendiente').order_by('-fecha_pedido')[:5]

    context = {
        'today': today,
        'ingresos_hoy': ingresos_hoy,
        'egresos_hoy': egresos_hoy,
        'ingresos_mes': ingresos_mes,
        'egresos_mes': egresos_mes,
        'balance_mes': balance_mes,
        'ventas_hoy': ventas_hoy,
        'ultimas_ventas': ultimas_ventas,
        'eventos_pendientes_count': eventos_pendientes_count,
        'eventos_proximos': eventos_proximos,
        'productos_sin_stock_count': productos_sin_stock_count,
        'productos_bajo_stock_count': productos_bajo_stock_count,
        'productos_stock_normal_count': productos_stock_normal_count,
        'pedidos_pendientes': pedidos_pendientes,
    }

    return render(request, 'home.html', context)

@login_required
def empleado_dashboard(request):
    """Dashboard para empleados"""
    # Verificar que sea empleado
    if not hasattr(request.user, 'profile') or request.user.profile.rol != 'Empleado':
        return redirect('home')

    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Ventas del empleado
    ventas_hoy = Venta.objects.filter(
        empleado=request.user.profile,
        fecha_creacion__date=today.date()
    )
    
    ventas_mes = Venta.objects.filter(
        empleado=request.user.profile,
        fecha_creacion__gte=start_of_month
    )

    # Estadísticas
    total_ventas_hoy = ventas_hoy.aggregate(
        total=Sum('total')
    )['total'] or Decimal('0')

    total_ventas_mes = ventas_mes.aggregate(
        total=Sum('total')
    )['total'] or Decimal('0')

    context = {
        'today': today,
        'total_ventas_hoy': total_ventas_hoy,
        'total_ventas_mes': total_ventas_mes,
        'cantidad_ventas_hoy': ventas_hoy.count(),
        'cantidad_ventas_mes': ventas_mes.count(),
        'ultimas_ventas': ventas_hoy.order_by('-fecha_creacion')[:5],
    }

    return render(request, 'usuarios/empleado_dashboard.html', context)

# Vistas de gestión de administradores
@login_required
@user_passes_test(lambda u: u.is_superuser)
def crear_administrador(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = ProfileForm(request.POST)
        
        print("Processing form submission...")  # Debug log
        
        if user_form.is_valid() and profile_form.is_valid():
            try:
                with transaction.atomic():
                    # Create user first
                    user = user_form.save()
                    
                    # Delete existing profile if it exists
                    Profile.objects.filter(user=user).delete()
                    
                    # Create new profile
                    profile = profile_form.save(commit=False)
                    profile.user = user
                    profile.rol = 'Administrador'
                    profile.save()
                    
                    print(f"Administrator created successfully: {user.username}")  # Debug log
                    return redirect('listar_administradores')
                    
            except IntegrityError as e:
                print(f"IntegrityError: {e}")  # Debug log
                user.delete()  # Rollback user creation
                user_form.add_error(None, f"Error al crear el administrador: {str(e)}")
            except Exception as e:
                print(f"Unexpected error: {e}")  # Debug log
                if 'user' in locals():
                    user.delete()  # Rollback user creation
                user_form.add_error(None, f"Error inesperado al crear el administrador: {str(e)}")
        else:
            print("Form validation errors:")  # Debug log
            print("User form errors:", user_form.errors)
            print("Profile form errors:", profile_form.errors)
    else:
        user_form = UserForm()
        profile_form = ProfileForm()
    
    return render(request, 'usuarios/Administrador/crear_administrador.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'form_errors': user_form.errors or profile_form.errors,
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def listar_administradores(request):
    administradores = Profile.objects.filter(
        rol='Administrador',
        user__is_superuser=False  # Excluir superusuarios
    )
    
    # Aplicar filtros
    nombre = request.GET.get('nombre', '')
    email = request.GET.get('email', '')
    telefono = request.GET.get('telefono', '')

    if nombre:
        administradores = administradores.filter(nombre_completo__icontains=nombre)
    if email:
        administradores = administradores.filter(user__email__icontains(email))
    if telefono:
        administradores = administradores.filter(telefono__icontains(telefono))

    return render(request, 'usuarios/Administrador/listar_administradores.html', {
        'administradores': administradores
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def editar_administrador(request, admin_id):
    admin = get_object_or_404(Profile, id=admin_id)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=admin.user, edit_mode=True)
        profile_form = ProfileForm(request.POST, instance=admin)
        
        if user_form.is_valid() and profile_form.is_valid():
            request.session['admin_edit_data'] = {
                'username': user_form.cleaned_data['username'],
                'email': user_form.cleaned_data['email'],
                'nombre_completo': profile_form.cleaned_data['nombre_completo'],
                'telefono': profile_form.cleaned_data['telefono'],
                'direccion': profile_form.cleaned_data['direccion'],
                'password': user_form.cleaned_data.get('password', ''),
                'rol': admin.rol
            }
            return redirect('confirmar_edicion_admin', admin_id=admin.id)
    else:
        user_form = UserForm(request.POST, instance=admin.user, edit_mode=True)
        profile_form = ProfileForm(request.POST, instance=admin)
    
    return render(request, 'usuarios/Administrador/editar_administrador.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'admin': admin
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def confirmar_edicion_admin(request, admin_id):
    admin = get_object_or_404(Profile, id=admin_id)
    new_data = request.session.get('admin_edit_data', {})

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update user data
                user = admin.user
                user.username = new_data.get('username', user.username)
                user.email = new_data.get('email', user.email)
                
                if new_data.get('password'):
                    user.set_password(new_data['password'])
                
                user.save()

                # Update profile data
                admin.nombre_completo = new_data.get('nombre_completo', admin.nombre_completo)
                admin.telefono = new_data.get('telefono', admin.telefono)
                admin.direccion = new_data.get('direccion', admin.direccion)
                admin.save()

                # Clear session data
                if 'admin_edit_data' in request.session:
                    del request.session['admin_edit_data']

                messages.success(request, '¡Administrador actualizado exitosamente!')
                return redirect('listar_administradores')

        except Exception as e:
            messages.error(request, f'Error al actualizar el administrador: {str(e)}')
            return redirect('editar_administrador', admin_id=admin.id)

    return render(request, 'usuarios/Administrador/confirmar_edicion_admin.html', {
        'admin': admin,
        'new_data': new_data,
        'show_password_change': bool(new_data.get('password'))
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def eliminar_administrador(request, admin_id):
    profile = get_object_or_404(Profile, id=admin_id)
    if request.method == 'POST':
        profile.user.delete()
        profile.delete()
        return redirect('listar_administradores')
    return render(request, 'usuarios/Administrador/eliminar_administrador.html', {'administrador': profile})

# Vistas de gestión de empleados
@login_required
@user_passes_test(is_admin_or_superuser)
def crear_empleado(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST)
        profile_form = ProfileForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            try:
                with transaction.atomic():
                    # Check for existing email globally
                    email = user_form.cleaned_data['email']
                    if User.objects.filter(email=email).exists():
                        messages.error(request, 'Este correo electrónico ya está registrado')
                        return render(request, 'usuarios/Empleado/crear_empleado.html', {
                            'user_form': user_form,
                            'profile_form': profile_form
                        })

                    # Create the user
                    user = user_form.save(commit=False)
                    user.set_password(user_form.cleaned_data['password'])
                    user.save()
                    
                    # Store data for confirmation
                    request.session['empleado_temp_data'] = {
                        'user_id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'nombre_completo': profile_form.cleaned_data['nombre_completo'],
                        'telefono': profile_form.cleaned_data['telefono'],
                        'direccion': profile_form.cleaned_data['direccion'],
                        'fecha_contratacion': profile_form.cleaned_data['fecha_contratacion'].strftime('%Y-%m-%d')
                    }
                    
                    return redirect('confirmar_creacion_empleado')
                    
            except Exception as e:
                messages.error(request, f'Error al crear el empleado: {str(e)}')
                if 'user' in locals():
                    user.delete()
        else:
            for form in [user_form, profile_form]:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        user_form = UserForm()
        profile_form = ProfileForm()
    
    return render(request, 'usuarios/Empleado/crear_empleado.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
@user_passes_test(is_admin_or_superuser)
def confirmar_creacion_empleado(request):
    temp_data = request.session.get('empleado_temp_data', {})
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # First check if the user still exists (might have been deleted)
                try:
                    user = User.objects.get(id=temp_data['user_id'])
                except User.DoesNotExist:
                    messages.error(request, 'Error: El usuario no existe')
                    return redirect('crear_empleado')

                # Check if profile already exists
                if hasattr(user, 'profile'):
                    user.delete()
                    messages.error(request, 'Error: Ya existe un perfil para este usuario')
                    return redirect('crear_empleado')

                # Create the profile
                profile = Profile(
                    user=user,
                    rol='Empleado',
                    nombre_completo=temp_data['nombre_completo'],
                    telefono=temp_data['telefono'],
                    direccion=temp_data['direccion'],
                    fecha_contratacion=temp_data['fecha_contratacion']
                )
                profile.save()
                
                # Clear the session data
                if 'empleado_temp_data' in request.session:
                    del request.session['empleado_temp_data']
                
                messages.success(request, 'Empleado creado exitosamente')
                return redirect('listar_empleados')
                
        except IntegrityError as e:
            # If something goes wrong, delete the user to prevent orphaned users
            if 'user' in locals():
                user.delete()
            messages.error(request, 'Error: Ya existe un perfil para este usuario')
            return redirect('crear_empleado')
        except Exception as e:
            if 'user' in locals():
                user.delete()    
            messages.error(request, f'Error al crear el empleado: {str(e)}')
            return redirect('crear_empleado')
    
    return render(request, 'usuarios/Empleado/confirmar_creacion_empleado.html', {
        'data': temp_data
    })

@login_required
@user_passes_test(is_admin_or_superuser)
def listar_empleados(request):
    """Vista para listar todos los empleados"""
    empleados = Profile.objects.filter(rol='Empleado')
    
    # Aplicar filtros
    nombre = request.GET.get('nombre', '')
    email = request.GET.get('email', '')
    telefono = request.GET.get('telefono', '')
    fecha_desde = request.GET.get('fecha_desde', '')
    fecha_hasta = request.GET.get('fecha_hasta', '')

    if nombre:
        empleados = empleados.filter(nombre_completo__icontains=nombre)
    if email:
        empleados = empleados.filter(user__email__icontains(email))
    if telefono:
        empleados = empleados.filter(telefono__icontains(telefono))
    if fecha_desde:
        empleados = empleados.filter(fecha_contratacion__gte=fecha_desde)
    if fecha_hasta:
        empleados = empleados.filter(fecha_contratacion__lte=fecha_hasta)

    return render(request, 'usuarios/Empleado/listar_empleados.html', {
        'empleados': empleados
    })

@login_required
@user_passes_test(is_admin_or_superuser)
def editar_empleado(request, empleado_id):
    empleado = get_object_or_404(Profile, id=empleado_id, rol='Empleado')
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=empleado.user, edit_mode=True)
        profile_form = ProfileForm(request.POST, instance=empleado)
        
        if user_form.is_valid() and profile_form.is_valid():
            try:
                request.session['empleado_edit_data'] = {
                    'username': user_form.cleaned_data['username'],
                    'email': user_form.cleaned_data['email'],
                    'nombre_completo': profile_form.cleaned_data['nombre_completo'],
                    'telefono': profile_form.cleaned_data['telefono'],
                    'direccion': profile_form.cleaned_data['direccion'],
                    'fecha_contratacion': profile_form.cleaned_data['fecha_contratacion'].strftime('%Y-%m-%d'),
                    'password': user_form.cleaned_data.get('password', '')
                }
                return redirect('confirmar_edicion_empleado', empleado_id=empleado.id)
            except IntegrityError:
                messages.error(request, 'Error: Ya existe un usuario con ese nombre de usuario o correo electrónico')
        else:
            for form in [user_form, profile_form]:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
    else:
        user_form = UserForm(request.POST, instance=empleado.user, edit_mode=True)
        profile_form = ProfileForm(request.POST, instance=empleado)
    
    return render(request, 'usuarios/Empleado/editar_empleado.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'empleado': empleado
    })

@login_required
@user_passes_test(is_admin_or_superuser)
def eliminar_empleado(request, empleado_id):
    profile = get_object_or_404(Profile, id=empleado_id)
    if request.method == 'POST':
        profile.user.delete()
        profile.delete()
        return redirect('listar_empleados')
    return render(request, 'usuarios/Empleado/eliminar_empleado.html', {'empleado': profile})

@login_required
@user_passes_test(is_admin_or_superuser)
def confirmar_edicion_empleado(request, empleado_id):
    empleado = get_object_or_404(Profile, id=empleado_id)
    new_data = request.session.get('empleado_edit_data', {})
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                user = empleado.user
                user.username = new_data.get('username', user.username)
                user.email = new_data.get('email', user.email)
                if new_data.get('password'):
                    user.set_password(new_data['password'])
                user.save()

                empleado.nombre_completo = new_data.get('nombre_completo', empleado.nombre_completo)
                empleado.telefono = new_data.get('telefono', empleado.telefono)
                empleado.direccion = new_data.get('direccion', empleado.direccion)
                empleado.fecha_contratacion = new_data.get('fecha_contratacion', empleado.fecha_contratacion)
                empleado.save()

                if 'empleado_edit_data' in request.session:
                    del request.session['empleado_edit_data']

                messages.success(request, '¡Empleado actualizado exitosamente!')
                return redirect('listar_empleados')

        except IntegrityError as e:
            messages.error(request, f'Error de integridad: {str(e)}')
            return redirect('editar_empleado', empleado_id=empleado.id)
        except Exception as e:
            messages.error(request, f'Error al actualizar el empleado: {str(e)}')
            return redirect('editar_empleado', empleado_id=empleado.id)

    return render(request, 'usuarios/Empleado/confirmar_edicion_empleado.html', {
        'empleado': empleado,
        'new_data': new_data
    })

# Vistas de recuperación de contraseña
def recuperar_password(request):
    """Vista para iniciar el proceso de recuperación de contraseña"""
    if request.method == "POST":
        email = request.POST.get("email")
        if email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return render(request, 'usuarios/recuperar.html', {'error': 'El correo no está registrado.'})

            # Generar un nuevo PIN
            pin_code = get_random_string(6, allowed_chars='0123456789')

            # Crear o actualizar el PIN del usuario
            PIN.objects.update_or_create(user=user, defaults={'pin': pin_code})

            # Enviar el PIN al correo usando Amazon SES
            send_mail(
                'Recuperación de Contraseña',
                f'Tu PIN de recuperación es: {pin_code}',
                '',  # Cambia esto por la dirección de correo verificada
                [user.email],
                fail_silently=False,
            )
            return redirect('verificar_pin')
        else:
            return render(request, 'usuarios/recuperar.html', {'error': 'Por favor, introduce un correo electrónico.'})

    return render(request, 'usuarios/recuperar.html')

def verificar_pin(request):
    """Vista para verificar el PIN de recuperación"""
    if request.method == "POST":
        if 'email' in request.POST and 'pin' in request.POST:
            email = request.POST.get("email")
            pin = request.POST.get("pin")

            if email and pin:
                try:
                    user = User.objects.get(email=email)
                    pin_object = PIN.objects.get(user=user, pin=pin)

                    if pin_object.is_valid():
                        return render(request, 'usuarios/verificar_pin.html', {'email': email, 'valid_pin': True})

                    else:
                        return render(request, 'usuarios/verificar_pin.html', {'error': 'El PIN ha expirado.'})

                except (User.DoesNotExist, PIN.DoesNotExist):
                    return render(request, 'usuarios/verificar_pin.html', {'error': 'Correo o PIN incorrecto.'})

            return render(request, 'usuarios/verificar_pin.html', {'error': 'Por favor, completa todos los campos.'})

        elif 'new_password' in request.POST:
            new_password = request.POST.get('new_password')
            email = request.POST.get('email')

            if new_password and email:
                try:
                    user = User.objects.get(email=email)
                    # Validar la nueva contraseña usando las validaciones de Django
                    try:
                        validate_password(new_password, user)
                        user.set_password(new_password)
                        user.save()
                        return render(request, 'usuarios/verificar_pin.html',
                                      {'success': 'Contraseña cambiada exitosamente.', 'valid_pin': False})
                    except ValidationError as e:
                        return render(request, 'usuarios/verificar_pin.html',
                                      {'error': e.messages, 'valid_pin': True, 'email': email})

                except User.DoesNotExist:
                    return render(request, 'usuarios/verificar_pin.html',
                                  {'error': 'Usuario no encontrado.', 'valid_pin': True, 'email': email})

            else:
                return render(request, 'usuarios/verificar_pin.html',
                              {'error': 'Por favor, ingresa una nueva contraseña.', 'valid_pin': True, 'email': email})

    return render(request, 'usuarios/verificar_pin.html')

def reset_password(request, email):
    """Vista para restablecer la contraseña"""
    if request.method == "POST":
        new_password = request.POST.get("new_password")
        email = request.POST.get("email")

        if email and new_password:
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                return HttpResponse("Password reset successfully")
            except User.DoesNotExist:
                return HttpResponse("User not found")

    return render(request, 'usuarios/reset_password.html', {'email': email})

# Funciones de utilidad
def generar_pin():
    """Genera un PIN aleatorio de 6 dígitos"""
    return str(random.randint(100000, 999999))

def enviar_pin(request):
    """Envía el PIN de recuperación por correo electrónico"""
    if request.method == "POST":
        email = request.POST.get("email")
        if email:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return render(request, 'usuarios/recuperar.html', {'error': 'El correo no está registrado.'})

            # Generar un nuevo PIN
            pin_code = get_random_string(6, allowed_chars='0123456789')

            # Crear o actualizar el PIN del usuario
            PIN.objects.update_or_create(user=user, defaults={'pin': pin_code})

            # Enviar el PIN al correo usando Amazon SES
            send_mail(
                'Recuperación de Contraseña',
                f'Tu PIN de recuperación es: {pin_code}',
                '',  # Dirección de correo desde la que se envía
                [user.email],  # Dirección de correo del usuario que recibe el PIN
                fail_silently=False,
            )
            return redirect('verificar_pin')
        else:
            return render(request, 'usuarios/recuperar.html', {'error': 'Por favor, introduce un correo electrónico.'})

    return render(request, 'usuarios/recuperar.html')





