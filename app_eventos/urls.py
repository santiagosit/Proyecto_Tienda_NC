from django.urls import path
from . import views

urlpatterns = [
    path('eventos/', views.listar_eventos, name='listar_eventos'),
    path('eventos/crear/', views.crear_evento, name='crear_evento'),
    path('eventos/editar/<int:evento_id>/', views.editar_evento, name='editar_evento'),
    path('eventos/eliminar/<int:evento_id>/', views.eliminar_evento, name='eliminar_evento'),
    path('eventos/confirmar-edicion/<int:evento_id>/', views.confirmar_edicion_evento, name='confirmar_edicion_evento'),
]