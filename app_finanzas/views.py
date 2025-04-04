# Importaciones de Django
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils import timezone

# Importaciones locales
from .models import Ingreso, Egreso
from .forms import EgresoForm
from app_usuarios.utils import is_admin_or_superuser, is_employee_or_above

# Vistas de ingresos
@login_required
@user_passes_test(is_admin_or_superuser)
def listar_ingresos(request):
    """Vista para listar todos los ingresos"""
    # Obtener todos los ingresos (ventas y personalizados)
    ingresos = Ingreso.objects.select_related('venta').all().order_by('-fecha')
    
    # Aplicar filtros si existen
    venta_id = request.GET.get('venta')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')

    if venta_id:
        ingresos = ingresos.filter(venta__id=venta_id)
    if fecha_desde:
        ingresos = ingresos.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        ingresos = ingresos.filter(fecha__lte=fecha_hasta)

    return render(request, 'finanzas/listar_ingresos.html', {
        'ingresos': ingresos,
    })

@login_required
@user_passes_test(is_admin_or_superuser)
def detalle_ingreso(request, ingreso_id):
    ingreso = get_object_or_404(Ingreso, id=ingreso_id)

    context = {
        'ingreso': ingreso,
    }

    if ingreso.venta:
        # Calcular totales usando los campos correctos del modelo VentaDetalle
        detalles = ingreso.venta.detalles.all()
        total = sum(detalle.precio_total for detalle in detalles)
        context.update({
            'detalles': detalles,
            'total': total,
            'subtotal': ingreso.venta.subtotal,  # Using the property from Venta model
            'iva': ingreso.venta.iva  # Using the property from Venta model
        })

    return render(request, 'finanzas/detalle_ingreso.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def eliminar_ingreso(request, ingreso_id):
    """Vista para eliminar un ingreso"""
    ingreso = get_object_or_404(Ingreso, id=ingreso_id)
    if request.method == 'POST':
        ingreso.delete()
        messages.success(request, 'Ingreso eliminado exitosamente.')
        return redirect('listar_ingresos')
    return render(request, 'finanzas/eliminar_ingreso.html', {'ingreso': ingreso})

@login_required
@user_passes_test(is_admin_or_superuser)
def crear_ingreso_personalizado(request):
    """Vista para crear un ingreso personalizado"""
    if request.method == 'POST':
        try:
            monto = request.POST.get('monto')
            if monto:
                monto = Decimal(monto)
                descripcion = request.POST.get('descripcion', '')
                
                ingreso = Ingreso.objects.create(
                    monto=monto,
                    descripcion=descripcion,
                    tipo='personalizado',
                    fecha=timezone.now()
                )
                
                messages.success(request, f'Ingreso personalizado de ${monto:,.2f} creado exitosamente.')
                return redirect('listar_ingresos')
            else:
                messages.error(request, 'El monto es requerido.')
        except InvalidOperation:
            messages.error(request, 'Error en el monto: asegúrese de ingresar un número válido.')
        except Exception as e:
            messages.error(request, f'Error al crear el ingreso: {str(e)}')
    
    return render(request, 'finanzas/crear_ingreso_personalizado.html')

# Vistas de egresos
@login_required
@user_passes_test(is_admin_or_superuser)
def listar_egresos(request):
    """Vista para listar todos los egresos"""
    egresos_pedidos = Egreso.objects.filter(tipo='pedido').select_related('pedido').order_by('-fecha')
    egresos_personalizados = Egreso.objects.filter(tipo='personalizado').order_by('-fecha')
    
    return render(request, 'finanzas/listar_egresos.html', {
        'egresos_pedidos': egresos_pedidos,
        'egresos_personalizados': egresos_personalizados,
    })

@login_required
@user_passes_test(is_admin_or_superuser)
def detalle_egreso(request, egreso_id):
    """Vista para ver el detalle de un egreso específico"""
    egreso = get_object_or_404(Egreso, id=egreso_id)

    if egreso.tipo == 'pedido' and egreso.pedido is not None:
        # Usar .all() para acceder a los detalles a través del related_name
        detalles = egreso.pedido.detalles.all()
        # Calcular el total usando la propiedad subtotal de cada detalle
        total = sum(detalle.subtotal for detalle in detalles)
    else:
        detalles = None
        total = egreso.monto

    context = {
        'egreso': egreso,
        'detalles': detalles,
        'total': total,
    }
    return render(request, 'finanzas/detalle_egreso.html', context)

@login_required
@user_passes_test(is_admin_or_superuser)
def crear_egreso_personalizado(request):
    """Vista para crear un nuevo egreso personalizado"""
    if request.method == 'POST':
        form = EgresoForm(request.POST)
        if form.is_valid():
            egreso = form.save(commit=False)
            if egreso.tipo == 'personalizado':
                egreso.pedido = None
            egreso.save()
            return redirect('listar_egresos')
    else:
        form = EgresoForm()
    return render(request, 'finanzas/crear_egreso_personalizado.html', {'form': form})

@login_required
@user_passes_test(is_admin_or_superuser)
def eliminar_egreso(request, egreso_id):
    """Vista para eliminar un egreso"""
    egreso = get_object_or_404(Egreso, id=egreso_id)
    if request.method == 'POST':
        egreso.delete()
        messages.success(request, 'Egreso eliminado exitosamente.')
        return redirect('listar_egresos')
    return render(request, 'finanzas/eliminar_egreso.html', {'egreso': egreso})
