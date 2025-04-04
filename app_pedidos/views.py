# Django imports
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse

# Local imports
from app_usuarios.utils import is_admin_or_superuser, is_employee_or_above
from .models import PedidoDetalle, Pedido, Producto, Proveedor
from .forms import PedidoForm, ProveedorForm
from decimal import Decimal

# Protected views - Employee level access
@login_required
@user_passes_test(is_employee_or_above)
def listar_pedidos(request):
    pedidos = Pedido.objects.all()
    
    # Aplicar filtros si existen
    filters = {
        'id': request.GET.get('id'),
        'proveedor_id': request.GET.get('proveedor'),
        'fecha_pedido': request.GET.get('fecha'),
        'estado': request.GET.get('estado'),
    }
    
    # Aplicar cada filtro si tiene valor
    for key, value in filters.items():
        if value:
            pedidos = pedidos.filter(**{key: value})
    
    # Filtro especial para productos
    if query_producto := request.GET.get('producto'):
        pedidos = pedidos.filter(
            pedidodetalle__producto_id=query_producto
        ).distinct()

    context = {
        'pedidos': pedidos,
        'proveedores': Proveedor.objects.all(),
        'productos': Producto.objects.all()
    }
    return render(request, 'pedidos/listar_pedidos.html', context)


# Protected views - Admin level access
@login_required
@user_passes_test(is_admin_or_superuser)
def listar_proveedores(request):
    proveedores = Proveedor.objects.all()
    return render(request, 'pedidos/listar_proveedores.html', {'proveedores': proveedores})


@login_required
@user_passes_test(is_admin_or_superuser)
def registrar_pedido(request):
    if request.method == 'POST':
        pedido_form = PedidoForm(request.POST)
        if pedido_form.is_valid():
            pedido = pedido_form.save()
            
            # Obtener los datos de los productos
            productos = request.POST.getlist('productos[]')
            cantidades = request.POST.getlist('cantidades[]')
            costos = request.POST.getlist('costos_unitarios[]')
            
            # Validar que haya al menos un producto
            if not productos:
                pedido.delete()
                messages.error(request, 'Debe agregar al menos un producto al pedido.')
                return render(request, 'pedidos/registrar_pedido.html', {
                    'pedido_form': PedidoForm(),
                    'productos': Producto.objects.all()
                })
            
            # Crear los detalles del pedido
            try:
                for producto_id, cantidad, costo in zip(productos, cantidades, costos):
                    PedidoDetalle.objects.create(
                        pedido=pedido,
                        producto_id=int(producto_id),
                        cantidad=int(cantidad),
                        costo_unitario=Decimal(costo)
                    )
                messages.success(request, 'Pedido registrado exitosamente.')
                return redirect('listar_pedidos')
            except Exception as e:
                pedido.delete()
                messages.error(request, f'Error al registrar el pedido: {str(e)}')
    else:
        pedido_form = PedidoForm()
    
    return render(request, 'pedidos/registrar_pedido.html', {
        'pedido_form': pedido_form,
        'productos': Producto.objects.all()
    })


@login_required
@user_passes_test(is_admin_or_superuser)
def registrar_proveedor(request):
    if request.method == 'POST':
        form = ProveedorForm(request.POST)
        if form.is_valid():
            proveedor = form.save()
            messages.success(request, '¡Proveedor registrado exitosamente!')
            return redirect('listar_proveedores')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = ProveedorForm()
    
    return render(request, 'pedidos/registrar_proveedor.html', {'form': form})


@login_required
@user_passes_test(is_admin_or_superuser)
def editar_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    
    if request.method == 'POST':
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Proveedor actualizado exitosamente!')
            return redirect('listar_proveedores')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = ProveedorForm(instance=proveedor)
    
    return render(request, 'pedidos/editar_proveedor.html', {
        'form': form,
        'proveedor': proveedor
    })


@login_required
@user_passes_test(is_admin_or_superuser)
def eliminar_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    
    if request.method == 'POST':
        try:
            proveedor.delete()
            messages.success(request, '¡Proveedor eliminado exitosamente!')
        except Exception as e:
            messages.error(request, f'No se pudo eliminar el proveedor: {str(e)}')
        return redirect('listar_proveedores')
    
    return render(request, 'pedidos/eliminar_proveedor.html', {'proveedor': proveedor})


@login_required
@user_passes_test(is_admin_or_superuser)
def actualizar_estado_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    
    if pedido.estado == 'recibido':
        messages.error(request, 'No se puede modificar un pedido ya recibido.')
        return redirect('listar_pedidos')

    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado:
            pedido.estado = nuevo_estado
            pedido.save()
            
            if nuevo_estado == 'recibido':
                # Actualizar stock cuando el pedido se marca como recibido
                for detalle in pedido.detalles.all():  # Changed from pedido.detalles()
                    detalle.actualizar_stock()
                messages.success(request, 'Pedido marcado como recibido y stock actualizado.')
            else:
                messages.success(request, 'Estado del pedido actualizado exitosamente.')
                
            return redirect('listar_pedidos')
    
    return render(request, 'pedidos/actualizar_estado_pedido.html', {'pedido': pedido})


# Utility views
@login_required
@user_passes_test(is_admin_or_superuser)
def detalles_pedido(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)
    detalles = pedido.detalles.all()
    return render(request, 'pedidos/detalles_pedido.html', {
        'pedido': pedido,
        'detalles': detalles
    })


def filtro_opciones(request):
    filtro = request.GET.get('filtro')
    opciones_html = ''

    opciones_map = {
        'producto': (Producto, 'nombre'),
        'proveedor': (Proveedor, 'nombre'),
        'fecha': None,
        'estado': [
            ('pedido', 'Pedido'),
            ('en camino', 'En camino'),
            ('recibido', 'Recibido')
        ]
    }

    if filtro in ['producto', 'proveedor']:
        model, field = opciones_map[filtro]
        items = model.objects.all()
        opciones_html = f'<select name="{filtro}">'
        opciones_html += ''.join(
            f'<option value="{item.id}">{getattr(item, field)}</option>'
            for item in items
        )
        opciones_html += '</select>'
    elif filtro == 'fecha':
        opciones_html = '<input type="date" name="fecha">'
    elif filtro == 'estado':
        opciones_html = '<select name="estado">'
        opciones_html += ''.join(
            f'<option value="{value}">{label}</option>'
            for value, label in opciones_map['estado']
        )
        opciones_html += '</select>'

    return JsonResponse({'opciones_html': opciones_html})
