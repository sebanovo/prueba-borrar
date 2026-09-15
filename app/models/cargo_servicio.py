from django.db import models
from app.models.cargo import Cargo
from app.models.servicio import Servicio

class CargoServicio(models.Model):
    cargo = models.ForeignKey(Cargo, on_delete=models.CASCADE, related_name="detalles")
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT, related_name="en_cargos")
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    class Meta:
        db_table = "cargos_servicios"
        unique_together = [("cargo", "servicio")]  # un servicio por cargo (ajusta si deseas múltiples)

    def save(self, *args, **kwargs):
        self.subtotal = (self.cantidad or 0) * (self.precio_unitario or 0)
        super().save(*args, **kwargs)
        # Actualiza total del cargo cada vez que cambie un detalle
        self.cargo.recomputar_total()

    def __str__(self):
        return f"{self.servicio} x {self.cantidad} = {self.subtotal}"
