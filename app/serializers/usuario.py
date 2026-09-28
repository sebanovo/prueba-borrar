# app/serializers/usuario.py
from rest_framework import serializers
from app.models.usuario import Usuario

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_MB = 2


class UsuarioListSerializer(serializers.ModelSerializer):
    # devuelve la URL absoluta si hay request en el contexto
    foto = serializers.ImageField(read_only=True, allow_null=True, use_url=True)
    residencia_activa = serializers.SerializerMethodField(read_only=True)
    propiedad_activa = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Usuario
        fields = [
            "id", "email", "username", "ci", "rol", "nombre",
            "telefono", "foto", "fecha_nacimiento", "is_active",
            "date_joined",
            "residencia_activa",
            "propiedad_activa",
        ]
        read_only_fields = ["id", "date_joined"]

    def get_residencia_activa(self, obj):
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


# --------- CREATE ----------
class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6)
    foto = serializers.ImageField(required=False, allow_null=True, use_url=True)

    class Meta:
        model = Usuario
        fields = [
            "id", "email", "username", "ci", "rol", "nombre",
            "telefono", "foto", "fecha_nacimiento", "password",
        ]
        extra_kwargs = {
            "telefono": {"required": False, "allow_null": True, "allow_blank": True},
            "fecha_nacimiento": {"required": False, "allow_null": True},
        }

    # Validaciones recomendadas para la imagen
    def validate_foto(self, value):
        if value is None:
            return value
        if value.size > MAX_IMAGE_MB * 1024 * 1024:
            raise serializers.ValidationError(f"La imagen no debe superar {MAX_IMAGE_MB}MB.")
        if getattr(value, "content_type", None) and value.content_type not in ALLOWED_IMAGE_TYPES:
            raise serializers.ValidationError("Formatos permitidos: JPG, PNG, WEBP.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        usuario = Usuario(**validated_data)
        usuario.set_password(password)
        usuario.save()
        return usuario


# --------- UPDATE / PATCH ----------
class UsuarioUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False, min_length=6)
    foto = serializers.ImageField(required=False, allow_null=True, use_url=True)

    class Meta:
        model = Usuario
        fields = [
            "email", "username", "ci", "rol", "nombre",
            "telefono", "foto", "fecha_nacimiento", "password", "is_active",
        ]

    def validate_foto(self, value):
        if value is None:
            return value
        if value.size > MAX_IMAGE_MB * 1024 * 1024:
            raise serializers.ValidationError(f"La imagen no debe superar {MAX_IMAGE_MB}MB.")
        if getattr(value, "content_type", None) and value.content_type not in ALLOWED_IMAGE_TYPES:
            raise serializers.ValidationError("Formatos permitidos: JPG, PNG, WEBP.")
        return value

    def update(self, instance, validated_data):
        pwd = validated_data.pop("password", None)

        # Permitir “borrar” la foto si viene explícitamente vacía o null
        if "foto" in validated_data and validated_data["foto"] is None:
            if instance.foto:
                instance.foto.delete(save=False)

        for k, v in validated_data.items():
            setattr(instance, k, v)

        if pwd:
            instance.set_password(pwd)
        instance.save()
        return instance
