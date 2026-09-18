from rest_framework import serializers
from app.models.usuario import Usuario

class UsuarioCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=6)

    class Meta:
        model = Usuario
        fields = [
            "id", "email", "username", "ci", "rol", "nombre",
            "telefono", "foto", "fecha_nacimiento", "password"
        ]
        extra_kwargs = {
            "telefono": {"required": False, "allow_null": True, "allow_blank": True},
            "foto": {"required": False, "allow_null": True},
            "fecha_nacimiento": {"required": False, "allow_null": True},
        }

    def create(self, validated_data):
        password = validated_data.pop("password")
        usuario = Usuario(**validated_data)
        usuario.set_password(password)  # encripta la contraseña
        usuario.save()
        return usuario
