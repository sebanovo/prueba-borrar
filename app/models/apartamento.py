# app/models/apartamento.py
from django.db import models

class Apartamento(models.Model):
    numero = models.CharField(max_length=20, unique=True)   # ajusta a tu realidad
    bloque = models.CharField(max_length=10, blank=True, null=True)
    estado = models.CharField(max_length=20, default='DISPONIBLE')  # opcional
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'apartamentos'
        ordering = ['numero']

    def __str__(self):
        return f"Apto {self.numero}"
