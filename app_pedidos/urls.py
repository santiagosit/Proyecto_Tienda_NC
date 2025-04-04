from django.urls import path

from . import views
from .views import registrar_proveedor, listar_proveedores, registrar_pedido, listar_pedidos, actualizar_estado_pedido, \
    detalles_pedido

urlpatterns = [
    path('proveedores/registrar/', views.registrar_proveedor, name='registrar_proveedor'),
    path('proveedores/', views.listar_proveedores, name='listar_proveedores'),
    path('pedidos/registrar/', registrar_pedido, name='registrar_pedido'),
    path('pedidos/', listar_pedidos, name='listar_pedidos'),
    path('pedidos/actualizar_estado/<int:pedido_id>/', actualizar_estado_pedido, name='actualizar_estado_pedido'),
    path('pedidos/detalles/<int:pedido_id>/', detalles_pedido, name='detalles_pedido'),
    path('proveedores/eliminar/<int:proveedor_id>/', views.eliminar_proveedor, name='eliminar_proveedor'),
    path('proveedores/editar/<int:proveedor_id>/', views.editar_proveedor, name='editar_proveedor'),
]
