from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import IntegrityError, transaction

from app_usuarios.utils import is_employee_or_above, is_admin_or_superuser
from .models import Evento, Cliente



@login_required
def listar_eventos(request):
    eventos = Evento.objects.all().order_by('-fecha_evento')
    
    # Aplicar filtros
    cliente = request.GET.get('cliente', '')
    telefono = request.GET.get('telefono', '')
    fecha = request.GET.get('fecha', '')
    descripcion = request.GET.get('descripcion', '')

    if cliente:
        eventos = eventos.filter(cliente__nombre__icontains=cliente)
    if telefono:
        eventos = eventos.filter(cliente__telefono__icontains=telefono)
    if fecha:
        eventos = eventos.filter(fecha_evento__date=fecha)
    if descripcion:
        eventos = eventos.filter(descripcion__icontains=descripcion)

    return render(request, 'eventos/listar_eventos.html', {
        'eventos': eventos
    })

@login_required
@user_passes_test(is_admin_or_superuser)
def crear_evento(request):
    if request.method == 'POST':
        try:
            # Create cliente
            cliente = Cliente.objects.create(
                nombre=request.POST['nombre'],
                telefono=request.POST['telefono'],
                email=request.POST['email']
            )
            
            evento = Evento.objects.create(
                cliente=cliente,
                descripcion=request.POST['descripcion'],
                fecha_evento=request.POST['fecha_evento']
            )
            
            messages.success(request, '¡Evento creado exitosamente!')
            return redirect('listar_eventos')
        except IntegrityError as e:
            messages.error(request, 'Error: El correo electrónico ya está registrado')
            return render(request, 'eventos/crear_evento.html')
        except Exception as e:
            messages.error(request, f'Error al crear el evento: {str(e)}')
            return render(request, 'eventos/crear_evento.html')
    
    return render(request, 'eventos/crear_evento.html')

@login_required
@user_passes_test(is_admin_or_superuser)
def editar_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    
    if request.method == 'POST':
        return render(request, 'eventos/confirmar_edicion.html', {
            'evento': evento,
            'new_data': request.POST
        })
    
    return render(request, 'eventos/editar_evento.html', {'evento': evento})

@login_required
@user_passes_test(is_admin_or_superuser)
def confirmar_edicion_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update cliente
                evento.cliente.nombre = request.POST['nombre']
                evento.cliente.telefono = request.POST['telefono']
                evento.cliente.email = request.POST['email']
                evento.cliente.save()
                
                # Update evento
                evento.descripcion = request.POST['descripcion']
                evento.fecha_evento = request.POST['fecha_evento']
                evento.save()
                
                messages.success(request, '¡Evento actualizado exitosamente!')
                return redirect('listar_eventos')
        except IntegrityError as e:
            messages.error(request, 'Error: El correo electrónico ya está registrado')
            return redirect('editar_evento', evento_id=evento.id)
        except Exception as e:
            messages.error(request, f'Error al actualizar el evento: {str(e)}')
            return redirect('editar_evento', evento_id=evento.id)
    
    return render(request, 'eventos/confirmar_edicion.html', {
        'evento': evento,
        'new_data': request.POST
    })

@login_required
@user_passes_test(is_admin_or_superuser)
def eliminar_evento(request, evento_id):
    evento = get_object_or_404(Evento, id=evento_id)
    
    if request.method == 'POST':
        if request.POST.get('confirmar') == 'si':
            evento.delete()
            messages.success(request, 'Evento eliminado exitosamente.')
            return redirect('listar_eventos')
    
    return render(request, 'eventos/eliminar_evento.html', {'evento': evento})
