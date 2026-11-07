from django import forms
from .models import AppUser, UserType

class AppUserCreationForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control form-control-solid bg-transparent', 'placeholder': '••••••••'}),
        label="Contraseña"
    )

    class Meta:
        model = AppUser
        fields = ['first_name', 'last_name', 'email', 'user_type', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control form-control-solid bg-transparent', 'placeholder': 'Ej. Juan'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control form-control-solid bg-transparent', 'placeholder': 'Ej. Pérez'}),
            'email': forms.EmailInput(attrs={'class': 'form-control form-control-solid bg-transparent', 'placeholder': 'correo@ejemplo.com'}),
            'user_type': forms.Select(attrs={'class': 'form-select form-select-solid bg-transparent'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user



class LoginForm(forms.Form):
    email = forms.EmailField(
        label='Correo Electrónico',
        max_length=255, 
        required=True, 
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-solid bg-transparent',
            'placeholder': 'correo@ejemplo.com',
            'autocomplete': 'off'
        })
    )
    password = forms.CharField(
        label='Contraseña',
        max_length=128,
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-solid bg-transparent',
            'placeholder': 'Contraseña',
            'autocomplete': 'current-password'
        })
    )