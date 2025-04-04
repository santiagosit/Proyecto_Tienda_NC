from django.urls import path
from . import views
from .views import reporte_ingresos_egresos

urlpatterns = [
    path('reporte/', views.reporte_inventario, name='reporte_inventario'),
    path('exportar-reporte-excel/', views.exportar_reporte_excel, name='exportar_reporte_excel'),
    path('reporte-ingresos-egresos/', views.reporte_ingresos_egresos, name='reporte_ingresos_egresos'),
    path('exportar-reporte-financiero/', views.exportar_reporte_financiero, name='exportar_reporte_financiero'),
    path('exportar-reporte-pdf/', views.exportar_reporte_pdf, name='exportar_reporte_pdf'),
]