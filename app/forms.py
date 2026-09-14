from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from app.models.usuario import Usuario

class UsuarioCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Usuario
        fields = (
            "email", "username", "first_name", "last_name",
            "ci", "telefono", "fecha_nacimiento", "foto",
            "rol", "is_staff", "is_active",
        )

class UsuarioChangeForm(UserChangeForm):
    class Meta:
        model = Usuario
        fields = (
            "email", "username", "first_name", "last_name",
            "ci", "telefono", "fecha_nacimiento", "foto",
            "rol", "is_staff", "is_active", "is_superuser",
            "groups", "user_permissions",
        )
