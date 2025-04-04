from django.urls import path
from . import views
from .views import recuperar_password, verificar_pin,enviar_pin

urlpatterns = [
    # Usuarios
    path('', views.iniciar_sesion, name='login'),
    path('login/', views.iniciar_sesion, name='iniciar_sesion'),
    path('home/', views.home, name='home'),
    path('recuperar/', views.recuperar_password, name='recuperar_password'),
    path('verificar_pin/', views.verificar_pin, name='verificar_pin'),
    path('reset_password/<str:email>/', views.reset_password, name='reset_password'),
    path('logout/', views.logout_view, name='logout'),

    # Administradores
    path('crear_administrador/', views.crear_administrador, name='crear_administrador'),
    path('listar_administradores/', views.listar_administradores, name='listar_administradores'),
    path('editar_administrador/<int:admin_id>/', views.editar_administrador, name='editar_administrador'),
    path('eliminar_administrador/<int:admin_id>/', views.eliminar_administrador, name='eliminar_administrador'),
    path('administrador/confirmar-edicion/<int:admin_id>/', views.confirmar_edicion_admin, name='confirmar_edicion_admin'),
    path('administrador/<int:admin_id>/editar/', views.editar_administrador, name='editar_administrador'),
    path('administrador/<int:admin_id>/confirmar-edicion/', views.confirmar_edicion_admin, name='confirmar_edicion_admin'),

    # Empleados - agregar prefijo 'empleados/'
    path('empleados/crear/', views.crear_empleado, name='crear_empleado'),
    path('empleados/crear/confirmar/', views.confirmar_creacion_empleado, name='confirmar_creacion_empleado'),
    path('empleados/', views.listar_empleados, name='listar_empleados'),
    path('empleados/editar/<int:empleado_id>/', views.editar_empleado, name='editar_empleado'),
    path('empleados/eliminar/<int:empleado_id>/', views.eliminar_empleado, name='eliminar_empleado'),
    path('empleado/confirmar-edicion/<int:empleado_id>/', views.confirmar_edicion_empleado, name='confirmar_edicion_empleado'),
    path('empleado/<int:empleado_id>/editar/', views.editar_empleado, name='editar_empleado'),
    path('empleado/<int:empleado_id>/confirmar-edicion/', views.confirmar_edicion_empleado, name='confirmar_edicion_empleado'),
    path('empleado/dashboard/', views.empleado_dashboard, name='empleado_dashboard'),
]
