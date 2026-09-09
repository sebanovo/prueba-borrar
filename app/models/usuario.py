from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class Usuario(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        EMPLEADO = "EMPLEADO", "Empleado"
        RESIDENTE = "RESIDENTE", "Residente"


    email = models.EmailField(unique=True)
    ci = models.CharField(max_length=20, unique=True, validators=[RegexValidator(r'^\d+$', "El CI debe contener solo números.")], verbose_name="CI")
    rol = models.CharField(max_length=10, choices=Roles.choices, default=Roles.RESIDENTE)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    foto = models.ImageField(upload_to="usuarios/fotos/", blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)

    # Login por email
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "ci"]

    class Meta:
        db_table = "usuarios"

    def __str__(self):
        return f"{self.email} ({self.get_rol_display()})"
