from django import forms
from .models import Producto


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio', 'cantidad_stock', 'stock_minimo']
        labels = {
            'nombre': 'Nombre del Producto',
            'descripcion': 'Descripción',
            'precio': 'Precio',
            'cantidad_stock': 'Cantidad en Stock',
            'stock_minimo': 'Stock Mínimo',
        }
        widgets = {
            'descripcion': forms.Textarea(attrs={'cols': 80, 'rows': 5}),
        }
