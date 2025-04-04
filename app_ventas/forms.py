from django import forms
from .models import Venta, VentaDetalle
from  app_inventario.models import Producto

VentaDetalleFormSet = forms.inlineformset_factory(
    Venta, VentaDetalle, fields=['producto', 'cantidad', 'precio_unitario'], extra=1, can_delete=True
)


class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['observaciones']
