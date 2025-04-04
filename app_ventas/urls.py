from django.urls import path
from . import views
from .views import registrar_venta, detalle_venta, listar_ventas

urlpatterns = [
    path('registrar/', views.registrar_venta, name='registrar_venta'),
    path('ventas/<int:venta_id>/detalle/', views.detalle_venta, name='detalle_venta'),
    path('ventas/', views.listar_ventas, name='listar_ventas'),
    path('venta/confirmar/', views.confirmar_venta, name='confirmar_venta'),
    path('venta/<int:venta_id>/editar/', views.editar_venta, name='editar_venta'),
    path('mis-ventas/', views.mis_ventas, name='mis_ventas'),
]
