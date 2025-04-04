# Django imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum

# Local imports
from app_usuarios.utils import is_employee_or_above, is_admin_or_superuser
from app_inventario.models import Producto
from app_finanzas.models import Ingreso
from .models import Venta, VentaDetalle
from .forms import VentaForm

# Helper functions
def actualizar_producto_en_sesion(request, producto_id, cantidad, producto):
    """Actualiza la cantidad de un producto en la sesión y calcula totales."""
    try:
        productos_venta = request.session.get('productos_venta', [])
        
        # Convertir valores a Decimal para precisión en cálculos
        cantidad = int(cantidad)
        precio_unitario = Decimal(str(producto.precio))
        
        # Buscar si el producto ya existe
        producto_existente = None
        for p in productos_venta:
            if p['producto_id'] == producto_id:
                producto_existente = p
                break

        if producto_existente:
            nueva_cantidad = int(producto_existente['cantidad']) + cantidad
            if nueva_cantidad > producto.cantidad_stock:
                messages.error(
                    request,
                    f'Stock insuficiente para "{producto.nombre}". Disponible: {producto.cantidad_stock}'
                )
                return False
            
            producto_existente['cantidad'] = nueva_cantidad
            subtotal = precio_unitario * nueva_cantidad
            producto_existente['subtotal'] = str(subtotal)
        else:
            if cantidad > producto.cantidad_stock:
                messages.error(
                    request,
                    f'Stock insuficiente para "{producto.nombre}". Disponible: {producto.cantidad_stock}'
                )
                return False
                
            subtotal = precio_unitario * cantidad
            detalle = {
                'producto_id': producto.id,
                'producto_nombre': producto.nombre,
                'cantidad': cantidad,
                'precio_unitario': str(precio_unitario),
                'subtotal': str(subtotal)
            }
            productos_venta.append(detalle)

        # Actualizar total
        total = sum(Decimal(item['subtotal']) for item in productos_venta)
        
        request.session['productos_venta'] = productos_venta
        request.session['venta_total'] = str(total)
        request.session.modified = True
        return True

    except Exception as e:
        messages.error(request, f'Error al actualizar producto: {str(e)}')
        return False

def procesar_venta(request, venta_form):
    """Procesa y guarda una venta con sus detalles."""
    if venta_form.is_valid() and len(request.session['productos_venta']) > 0:
        venta = venta_form.save(commit=False)
        total_venta = 0
        venta.save()

        for detalle in request.session['productos_venta']:
            producto = Producto.objects.get(id=detalle['producto_id'])
            cantidad = int(detalle['cantidad'])
            precio_unitario = float(detalle['precio_unitario'])

            producto.cantidad_stock -= cantidad
            producto.save()

            VentaDetalle.objects.create(
                venta=venta,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario
            )
            total_venta += cantidad * precio_unitario

        venta.total = total_venta
        venta.save()

        request.session['productos_venta'] = []
        messages.success(request, 'Venta registrada exitosamente.')
        return True
    
    messages.error(request, 'Debe añadir al menos un producto para confirmar la venta.')
    return False

# View functions
@login_required
@user_passes_test(is_employee_or_above)
def registrar_venta(request):
    try:
        if not request.user.profile:
            messages.error(request, 'No tiene un perfil asociado.')
            return redirect('home')

        productos = Producto.objects.filter(cantidad_stock__gt=0)
        productos_venta = request.session.get('productos_venta', [])  # Define productos_venta here
        
        if request.method == 'POST':
            # Agregar producto
            if 'agregar_producto' in request.POST:
                producto_id = request.POST.get('producto')
                cantidad = int(request.POST.get('cantidad', 1))
                
                if not producto_id:
                    messages.error(request, 'Debe seleccionar un producto')
                    return redirect('registrar_venta')
                
                producto = get_object_or_404(Producto, id=producto_id)
                actualizar_producto_en_sesion(request, producto_id, cantidad, producto)
                return redirect('registrar_venta')

            # Eliminar producto
            elif 'eliminar_producto' in request.POST:
                index = int(request.POST.get('eliminar_producto'))
                
                if 0 <= index < len(productos_venta):
                    productos_venta.pop(index)
                    # Recalcular total
                    total = sum(Decimal(item['subtotal']) for item in productos_venta)
                    request.session['venta_total'] = str(total)
                    request.session['productos_venta'] = productos_venta
                    request.session.modified = True
                    messages.success(request, 'Producto eliminado correctamente')
                return redirect('registrar_venta')

            # Confirmar venta
            elif 'confirmar_venta' in request.POST:
                if not productos_venta:
                    messages.error(request, 'No hay productos en la venta')
                    return redirect('registrar_venta')

                try:
                    with transaction.atomic():
                        total = Decimal(request.session.get('venta_total', '0'))
                        
                        # Crear la venta
                        venta = Venta.objects.create(
                            empleado=request.user.profile,
                            estado='pendiente',
                            total=total
                        )

                        # Crear los detalles (el modelo se encargará del stock)
                        for item in productos_venta:
                            producto = Producto.objects.get(id=item['producto_id'])
                            cantidad = int(item['cantidad'])
                            precio_unitario = Decimal(item['precio_unitario'])
                            
                            # Verificar stock antes de crear el detalle
                            if producto.cantidad_stock < cantidad:
                                raise ValueError(f'Stock insuficiente para {producto.nombre}')
                            
                            VentaDetalle.objects.create(
                                venta=venta,
                                producto=producto,
                                cantidad=cantidad,
                                precio_unitario=precio_unitario,
                                precio_total=Decimal(item['subtotal'])
                            )

                        # Completar venta
                        venta.completar_venta()

                        # Limpiar sesión
                        request.session['productos_venta'] = []
                        request.session['venta_total'] = '0'
                        request.session.modified = True
                        
                        messages.success(request, 'Venta registrada exitosamente')
                        if request.user.profile.rol == 'Empleado':
                            return redirect('detalle_venta', venta_id=venta.id)
                        return redirect('listar_ventas')

                except Exception as e:
                    messages.error(request, f'Error al procesar la venta: {str(e)}')
                    return redirect('registrar_venta')

        context = {
            'productos': productos,
            'productos_venta': productos_venta,
            'total': Decimal(request.session.get('venta_total', '0'))
        }
        return render(request, 'ventas/registrar_venta.html', context)

    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('home')

@login_required
@user_passes_test(is_employee_or_above)
def confirmar_venta(request):
    productos_venta = request.session.get('productos_venta', [])
    total = request.session.get('venta_total', '0')
    
    if request.method == 'POST' and 'confirmar' in request.POST:
        try:
            with transaction.atomic():
                venta = Venta.objects.create(
                    empleado=request.user.profile,
                    creado_por=request.user.profile,
                    estado='pendiente',
                    total=Decimal(total)
                )
                
                for item in productos_venta:
                    producto = Producto.objects.get(id=item['producto_id'])
                    VentaDetalle.objects.create(
                        venta=venta,
                        producto=producto,
                        cantidad=item['cantidad'],
                        precio_unitario=item['precio_unitario'],
                        precio_total=item['subtotal']
                    )
                    producto.cantidad_stock -= int(item['cantidad'])
                    producto.save()
                
                venta.completar_venta()
                request.session['productos_venta'] = []
                request.session['venta_total'] = '0'
                messages.success(request, 'Venta registrada exitosamente')
                if request.user.profile.rol == 'Empleado':
                    return redirect('detalle_venta', venta_id=venta.id)
                return redirect('listar_ventas')
                
        except Exception as e:
            messages.error(request, f'Error al procesar la venta: {str(e)}')
    
    return render(request, 'ventas/confirmar_venta.html', {
        'productos_venta': productos_venta,
        'total': total
    })

@login_required
@user_passes_test(is_employee_or_above)
def detalle_venta(request, venta_id):
    try:
        # Verificar si el usuario es empleado y es su venta
        if request.user.profile.rol == 'Empleado':
            venta = get_object_or_404(Venta, id=venta_id, empleado=request.user.profile)
            template = 'ventas/detalle_venta_empleado.html'
        else:
            venta = get_object_or_404(Venta, id=venta_id)
            template = 'ventas/detalle_venta.html'

        detalles = venta.detalles.all()
        
        context = {
            'venta': venta,
            'detalles': detalles,
            'subtotal': venta.subtotal,
            'total': venta.total
        }
        
        # Añadir IVA solo para vista de admin
        if request.user.profile.rol != 'Empleado':
            context['iva'] = venta.iva
        
        return render(request, template, context)
    except Exception as e:
        messages.error(request, f'Error al mostrar el detalle: {str(e)}')
        if request.user.profile.rol == 'Empleado':
            return redirect('mis_ventas')
        return redirect('listar_ventas')

@login_required
@user_passes_test(is_employee_or_above)
def listar_ventas(request):
    if request.user.profile.rol == 'Empleado':
        # Empleados solo ven sus ventas
        ventas = Venta.objects.filter(creado_por=request.user.profile)
    else:
        # Admins y superusers ven todas las ventas
        ventas = Venta.objects.all()
    
    return render(request, 'ventas/listar_ventas.html', {'ventas': ventas})

@login_required
@user_passes_test(is_admin_or_superuser)
def editar_venta(request, venta_id):
    venta = get_object_or_404(Venta, id=venta_id)
    detalles = venta.detalles.all()
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Actualizar datos básicos de la venta
                venta.estado = request.POST.get('estado', venta.estado)
                venta.observaciones = request.POST.get('observaciones', '')
                venta.modificado_por = request.user.profile
                
                # Actualizar detalles existentes
                detalles_actualizados = []
                for detalle in detalles:
                    cantidad = int(request.POST.get(f'cantidad_{detalle.id}', 0))
                    if cantidad > 0:
                        # Verificar stock disponible
                        stock_disponible = detalle.producto.cantidad_stock + detalle.cantidad
                        if cantidad <= stock_disponible:
                            detalle.cantidad = cantidad
                            detalle.save()
                            detalles_actualizados.append(detalle.id)
                        else:
                            messages.error(request, f'Stock insuficiente para {detalle.producto.nombre}')
                            raise ValueError(f'Stock insuficiente para {detalle.producto.nombre}')
                
                # Eliminar detalles no actualizados
                venta.detalles.exclude(id__in=detalles_actualizados).delete()
                
                # Actualizar totales
                venta.actualizar_total()
                venta.save()
                
                messages.success(request, '¡Venta actualizada exitosamente!')
                return redirect('detalle_venta', venta_id=venta.id)

        except Exception as e:
            messages.error(request, f'Error al actualizar la venta: {str(e)}')
            return redirect('editar_venta', venta_id=venta.id)
    
    return render(request, 'ventas/editar_venta.html', {
        'venta': venta,
        'detalles': detalles
    })

@login_required
def mis_ventas(request):
    today = timezone.now().date()
    
    # Get employee's sales
    ventas = Venta.objects.filter(
        empleado=request.user.profile
    ).order_by('-fecha_creacion')

    # Calculate today's stats
    ventas_hoy = ventas.filter(fecha_creacion__date=today)
    total_ventas_hoy = ventas_hoy.aggregate(
        total=Sum('total')
    )['total'] or 0
    
    context = {
        'ventas': ventas,
        'total_ventas_hoy': total_ventas_hoy,
        'num_ventas_hoy': ventas_hoy.count(),
    }
    
    return render(request, 'ventas/mis_ventas.html', context)
