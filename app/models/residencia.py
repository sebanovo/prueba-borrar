from  django.db import models
from .usuario import Usuario


class Apartamento(models.Model):
    codigo = models.CharField(max_length=50, unique=True) 
    piso = models.IntegerField(null=True, blank=True)
    bloque = models.CharField(max_length=50, null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "apartamento"

    def __str__(self):
        return self.codigo

class Residente(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="estancias")
    apartamento = models.ForeignKey(Apartamento, on_delete=models.CASCADE, related_name="estancias")
    fecha_ingreso = models.DateField()
    fecha_salida = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "residentes"
        ordering = ["-fecha_ingreso"]

    def __str__(self):
        return f"{self.usuario.email} en {self.apartamento.codigo}"