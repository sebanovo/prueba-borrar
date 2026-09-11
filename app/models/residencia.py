from django.db import models
from django.conf import settings
from django.db.models import Q
from app.models.apartamento import Apartamento

Usuario = settings.AUTH_USER_MODEL  # "app.Usuario"

class Residencia(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='residencias')
    apartamento = models.ForeignKey(Apartamento, on_delete=models.PROTECT, related_name='residencias')
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(blank=True, null=True)  # null = residencia activa
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'residencias'
        ordering = ['-created_at']
        # Opcional pero MUY útil: solo una residencia ACTIVA por usuario
        constraints = [
            models.UniqueConstraint(
                fields=['usuario'],
                condition=Q(fecha_fin__isnull=True),
                name='uniq_residencia_activa_por_usuario'
            )
        ]

    def __str__(self):
        return f"{self.usuario} -> {self.apartamento} ({self.fecha_inicio} - {self.fecha_fin or 'activo'})"
