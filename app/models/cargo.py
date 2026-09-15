from django.db import models
from django.utils import timezone
from app.models.apartamento import Apartamento
from app.models.servicio import Servicio

class Cargo(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "PENDIENTE", "Pendiente"
        PAGADO = "PAGADO", "Pagado"
        VENCIDO = "VENCIDO", "Vencido"

    apartamento = models.ForeignKey(Apartamento, on_delete=models.PROTECT, related_name="cargos")
    # periodo de facturación (ajusta a tu preferencia)
    periodo = models.DateField(default=timezone.now)  # usa el día 1 del mes o la fecha que manejes
    estado = models.CharField(max_length=10, choices=Estado.choices, default=Estado.PENDIENTE)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    fecha_vencimiento = models.DateField(blank=True, null=True)
    notas = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "cargos"
        ordering = ["-periodo", "apartamento__numero"]

    def __str__(self):
        return f"Cargo {self.id} - Apto {self.apartamento.numero} - {self.periodo}"

    def recomputar_total(self):
        total = sum(d.subtotal for d in self.detalles.all())
        self.total = total
        self.save(update_fields=["total"])
        self._actualizar_estado()

    def aplicar_pago_aprobado(self):
        """Suma pagos aprobados y actualiza estado."""
        from app.models.pago import Pago  # import local para evitar ciclos
        pagado = sum(p.monto for p in self.pagos.filter(estado=Pago.Estado.APROBADO))
        self.pagado = pagado
        self.save(update_fields=["pagado"])
        self._actualizar_estado()

    def _actualizar_estado(self):
        if self.pagado >= self.total and self.total > 0:
            self.estado = Cargo.Estado.PAGADO
        elif 0 < self.pagado < self.total:
            self.estado = Cargo.Estado.PARCIAL
        else:
            self.estado = Cargo.Estado.PENDIENTE
        self.save(update_fields=["estado"])
