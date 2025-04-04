from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('listar', views.listar_productos, name='listar_productos'),
    path('registrar', views.registrar_producto, name='registrar_producto'),
    path('eliminar/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('modificar/<int:producto_id>/', views.modificar_producto, name='modificar_producto'),
]
