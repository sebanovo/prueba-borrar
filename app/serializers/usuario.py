from rest_framework import serializers
from app.models.usuario import Usuario

class UsuarioListSerializer(serializers.ModelSerializer):
    residencia_activa = serializers.SerializerMethodField(read_only=True)
    propiedad_activa  = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Usuario
        fields = [
            "id", "email", "username", "ci", "rol", "nombre",
            "telefono", "foto", "fecha_nacimiento", "is_active",
            "date_joined",
            "residencia_activa",     # 👈 nuevo
            "propiedad_activa",      # 👈 nuevo
        ]
        read_only_fields = ["id", "date_joined"]

    def get_residencia_activa(self, obj):
        # Ajusta el related_name si tu modelo lo usa (p.ej. obj.residencias)
        qs = getattr(obj, "residencia_set", None) or getattr(obj, "residencias", None)
        if qs is None:
            return None
        r = qs.filter(fecha_fin__isnull=True).select_related("apartamento").first()
        if not r:
            return None
        return {
            "id": r.id,
            "apartamento": {
                "id": r.apartamento.id,
                "numero": r.apartamento.numero,
                "bloque": getattr(r.apartamento, "bloque", None),
                "estado": getattr(r.apartamento, "estado", None),
            },
            "fecha_inicio": r.fecha_inicio.isoformat() if r.fecha_inicio else None,
        }

    def get_propiedad_activa(self, obj):
        qs = getattr(obj, "propiedad_set", None) or getattr(obj, "propiedades", None)
        if qs is None:
            return None
        p = qs.filter(fecha_fin__isnull=True).select_related("apartamento").first()
        if not p:
            return None
        return {
            "id": p.id,
            "apartamento": {
                "id": p.apartamento.id,
                "numero": p.apartamento.numero,
                "bloque": getattr(p.apartamento, "bloque", None),
                "estado": getattr(p.apartamento, "estado", None),
            },
            "fecha_inicio": p.fecha_inicio.isoformat() if p.fecha_inicio else None,
        }
# Para crear (password requerido)
class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6)

    class Meta:
        model = Usuario
        fields = [
            "id", "email", "username", "ci", "rol", "nombre",
            "telefono", "foto", "fecha_nacimiento", "password",
        ]
        extra_kwargs = {
            "telefono": {"required": False, "allow_null": True, "allow_blank": True},
            "foto": {"required": False, "allow_null": True},
            "fecha_nacimiento": {"required": False, "allow_null": True},
        }

    def create(self, validated_data):
        password = validated_data.pop("password")
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.save()
        return usuario

# Para actualizar (password opcional)
class UsuarioUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False, min_length=6)

    class Meta:
        model = Usuario
        fields = [
            "email", "username", "ci", "rol", "nombre",
            "telefono", "foto", "fecha_nacimiento", "password", "is_active",
        ]

    def update(self, instance, validated_data):
        pwd = validated_data.pop("password", None)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        if pwd:
            instance.set_password(pwd)
        instance.save()
        return instance