from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from .models import Profile

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        validators=[validate_password],
        help_text='La contraseña debe tener al menos 8 caracteres, números y letras'
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Confirmar contraseña'
    )

    def __init__(self, *args, **kwargs):
        self.edit_mode = kwargs.pop('edit_mode', False)
        super().__init__(*args, **kwargs)
        if self.edit_mode:
            self.fields['password'].required = False
            self.fields['confirm_password'].required = False

    def clean_username(self):
        username = self.cleaned_data.get('username')
        # Check across ALL users
        if User.objects.filter(username=username).exclude(pk=getattr(self.instance, 'pk', None)).exists():
            raise forms.ValidationError('Este nombre de usuario ya está en uso')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Check across ALL users
        if User.objects.filter(email=email).exclude(pk=getattr(self.instance, 'pk', None)).exists():
            raise forms.ValidationError('Este correo electrónico ya está registrado')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password:
            if password != confirm_password:
                self.add_error('confirm_password', 'Las contraseñas no coinciden')
                raise forms.ValidationError('Las contraseñas deben ser iguales')
        elif not self.edit_mode and not password:
            raise forms.ValidationError('La contraseña es requerida')
        
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get('password'):
            user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class ProfileForm(forms.ModelForm):
    telefono = forms.CharField(
        validators=[
            RegexValidator(
                regex=r'^\d{10}$',
                message='El número de teléfono debe tener 10 dígitos'
            )
        ],
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    fecha_contratacion = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True
    )
    
    class Meta:
        model = Profile
        fields = ['nombre_completo', 'telefono', 'direccion', 'fecha_contratacion']
        widgets = {
            'nombre_completo': forms.TextInput(attrs={'class': 'form-control'}),
            'direccion': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_contratacion': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if Profile.objects.filter(telefono=telefono).exclude(pk=getattr(self.instance, 'pk', None)).exists():
            raise forms.ValidationError('Este número de teléfono ya está registrado')
        return telefono