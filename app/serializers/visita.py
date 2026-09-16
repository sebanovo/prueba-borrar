from rest_framework import serializers
from django.db import transaction
from app.models.visita import Visita
from app.models.visitante import Visitante
from app.models.vehiculo import Vehiculo

class VisitaSerializer(serializers.ModelSerializer):
    visitante_nombre = serializers.CharField(source="visitante.nombre", read_only=True)
    apartamento_numero = serializers.CharField(source="apartamento.numero", read_only=True)
    vehiculo_placa = serializers.CharField(source="vehiculo.placa", read_only=True)

    class Meta:
        model = Visita
        fields = ["id", "visitante", "visitante_nombre", "apartamento", "apartamento_numero",
                  "vehiculo", "vehiculo_placa", "detalle", "fecha", "hora_inicio", "hora_salida",
                  "registrado_por", "cerrado_por", "created_at"]
        read_only_fields = ["registrado_por", "cerrado_por", "created_at"]

class VisitaRegistrarSerializer(serializers.Serializer):
    """
    Contrato para /visitas/registrar/:
    {
      "apartamento": 5,
      "detalle": "Reunión",
      "visitante": { "nombre": "...", "ci": "...", "celular": "..." },
      "vehiculo": { "placa": "ABC123", "descripcion": "...", "apartamento": 5, "pase_conocido": true }   // opcional
    }
    """
    apartamento = serializers.IntegerField()
    detalle = serializers.CharField(required=False, allow_blank=True)
    visitante = serializers.DictField()
    vehiculo = serializers.DictField(required=False)

    @transaction.atomic
    def create(self, validated_data):
        request = self.context.get("request")
        apto_id = validated_data["apartamento"]
        detalle = validated_data.get("detalle", "")

        # 1) Visitante: buscar por CI o (nombre+celular) o crear
        vdata = validated_data["visitante"]
        visitante = None
        ci = vdata.get("ci")
        if ci:
            visitante = Visitante.objects.filter(ci=ci).first()
        if not visitante:
            visitante = Visitante.objects.create(
                nombre=vdata.get("nombre", "").strip(),
                ci=vdata.get("ci"),
                celular=vdata.get("celular"),
            )

        # 2) Vehículo (opcional)
        vehiculo_obj = None
        veh = validated_data.get("vehiculo")
        if veh:
            placa = veh.get("placa")
            if placa:
                vehiculo_obj = Vehiculo.objects.filter(placa__iexact=placa).first()
                if not vehiculo_obj:
                    vehiculo_obj = Vehiculo.objects.create(
                        placa=placa.upper(),
                        descripcion=veh.get("descripcion"),
                        apartamento_id=veh.get("apartamento"),  # None si es visitante
                        pase_conocido=bool(veh.get("pase_conocido", False)),
                    )
                # Validación de pase_conocido ya se hace en model.clean()

        # 3) Crear visita
        visita = Visita.objects.create(
            visitante=visitante,
            apartamento_id=apto_id,
            vehiculo=vehiculo_obj,
            detalle=detalle,
            registrado_por=getattr(request, "user", None),
        )
        return visita

    def to_representation(self, visita: Visita):
        return VisitaSerializer(visita).data
