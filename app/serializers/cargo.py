from rest_framework import serializers
from app.models.cargo import Cargo
from app.models.cargo_servicio import CargoServicio
from app.models.servicio import Servicio

class CargoServicioItemSerializer(serializers.ModelSerializer):
    servicio_nombre = serializers.CharField(source="servicio.nombre", read_only=True)

    class Meta:
        model = CargoServicio
        fields = ["id", "servicio", "servicio_nombre", "cantidad", "precio_unitario", "subtotal"]
        read_only_fields = ["subtotal"]

class CargoSerializer(serializers.ModelSerializer):
    detalles = CargoServicioItemSerializer(many=True, required=False)
    apartamento_numero = serializers.CharField(source="apartamento.numero", read_only=True)

    class Meta:
        model = Cargo
        fields = ["id", "apartamento", "apartamento_numero", "periodo", "fecha_vencimiento",
                  "estado", "total", "pagado", "notas", "detalles"]
        read_only_fields = ["estado", "total", "pagado"]

    def create(self, validated_data):
        detalles_data = validated_data.pop("detalles", [])
        cargo = Cargo.objects.create(**validated_data)
        for item in detalles_data:
            CargoServicio.objects.create(cargo=cargo, **item)
        cargo.recomputar_total()
        return cargo

    def update(self, instance, validated_data):
        detalles_data = validated_data.pop("detalles", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()

        if detalles_data is not None:
            # estrategia simple: borrar y volver a crear
            instance.detalles.all().delete()
            for item in detalles_data:
                CargoServicio.objects.create(cargo=instance, **item)
            instance.recomputar_total()

        return instance
