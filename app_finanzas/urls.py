from django.urls import path
from . import views

urlpatterns = [
    # Ingresos
    path('ingresos/', views.listar_ingresos, name='listar_ingresos'),
    path('ingresos/crear-personalizado/', views.crear_ingreso_personalizado, name='crear_ingreso_personalizado'),
    path('ingresos/<int:ingreso_id>/detalle/', views.detalle_ingreso, name='detalle_ingreso'),
    path('ingresos/<int:ingreso_id>/eliminar/', views.eliminar_ingreso, name='eliminar_ingreso'),
    
    # Egresos
    path('egresos/', views.listar_egresos, name='listar_egresos'),
    path('egresos/crear-personalizado/', views.crear_egreso_personalizado, name='crear_egreso_personalizado'),
    path('egresos/<int:egreso_id>/detalle/', views.detalle_egreso, name='detalle_egreso'),
    path('egresos/<int:egreso_id>/eliminar/', views.eliminar_egreso, name='eliminar_egreso'),
]
