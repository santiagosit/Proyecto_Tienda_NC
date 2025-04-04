from django import forms
from .models import Pedido, PedidoDetalle, Proveedor

class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['proveedor']
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'form-control'}),
        }

class PedidoDetalleForm(forms.ModelForm):
    class Meta:
        model = PedidoDetalle
        fields = ['producto', 'cantidad', 'costo_unitario']

class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['nombre', 'telefono', 'email', 'direccion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
