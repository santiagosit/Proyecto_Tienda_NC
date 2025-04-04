from django import forms
from .models import Ingreso, Egreso

class IngresoForm(forms.ModelForm):
    class Meta:
        model = Ingreso
        fields = ['venta', 'monto', 'descripcion']
        widgets = {
            'venta': forms.Select(attrs={'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_monto(self):
        monto = self.cleaned_data.get('monto')
        if monto and monto < 0:
            raise forms.ValidationError('El monto no puede ser negativo')
        return monto

# app_finanzas/forms.py
class EgresoForm(forms.ModelForm):
    class Meta:
        model = Egreso
        fields = ['tipo', 'pedido', 'monto', 'descripcion', 'categoria']
        widgets = {
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'pedido': forms.Select(attrs={'class': 'form-control'}),
            'monto': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'categoria': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        pedido = cleaned_data.get('pedido')
        
        if tipo == 'pedido' and not pedido:
            raise forms.ValidationError('Debe seleccionar un pedido para egresos de tipo pedido')
        elif tipo == 'personalizado' and pedido:
            cleaned_data['pedido'] = None
            
        return cleaned_data
