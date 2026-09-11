# app/serializers.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from app.models.usuario import Usuario
from app.models.apartamento import Apartamento
from app.models.residencia import Residencia
from django.db import transaction
from django.utils import timezone


class EmailOrUsernameTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        identifier = attrs.get("email") or attrs.get("username")
        if not identifier:
            raise self.fail("no_active_account")
        attrs["username"] = identifier  # SimpleJWT espera 'username'
        return super().validate(attrs)

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["rol"] = getattr(user, "rol", None)
        token["name"] = f"{user.first_name} {user.last_name}".strip()
        return token

class ResidenciaSerializer(serializers.ModelSerializer):
    usuario_id = serializers.PrimaryKeyRelatedField(
        queryset=Usuario.objects.all(), source='usuario', write_only=True
    )
    apartamento_id = serializers.PrimaryKeyRelatedField(
        queryset=Apartamento.objects.all(), source='apartamento', write_only=True
    )

    # representación de solo lectura
    usuario = serializers.SerializerMethodField(read_only=True)
    apartamento = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Residencia
        fields = ('id', 'usuario_id', 'apartamento_id', 'fecha_inicio', 'fecha_fin',
                  'usuario', 'apartamento', 'created_at')
        read_only_fields = ('id', 'created_at', 'usuario', 'apartamento')

    def get_usuario(self, obj):
        return {
            "id": obj.usuario.id,
            "email": getattr(obj.usuario, 'email', None),
            "nombre": getattr(obj.usuario, 'first_name', None),
            "apellido": getattr(obj.usuario, 'last_name', None),
            "rol": getattr(obj.usuario, 'rol', None),
        }

    def get_apartamento(self, obj):
        return {"id": obj.apartamento.id, "numero": obj.apartamento.numero}

    def validate(self, data):
        usuario = data.get('usuario') or getattr(self.instance, 'usuario', None)
        fecha_inicio = data.get('fecha_inicio') or getattr(self.instance, 'fecha_inicio', None)
        fecha_fin = data.get('fecha_fin') if 'fecha_fin' in data else getattr(self.instance, 'fecha_fin', None)

        if fecha_fin and fecha_fin < fecha_inicio:
            raise serializers.ValidationError("La fecha_fin no puede ser anterior a la fecha_inicio.")

        # Validar que no existan DOS residencias activas para el mismo usuario
        if fecha_fin is None and usuario:
            existe_activa = Residencia.objects.filter(usuario=usuario, fecha_fin__isnull=True)
            if self.instance:
                existe_activa = existe_activa.exclude(pk=self.instance.pk)
            if existe_activa.exists():
                raise serializers.ValidationError("El usuario ya tiene una residencia activa.")
        return data
    
class ApartamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Apartamento
        fields = ('id', 'numero', 'bloque', 'estado', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate_numero(self, value):
        if not value.strip():
            raise serializers.ValidationError("El número de apartamento no puede estar vacío.")
        return value
    
class ResidenteAltaSerializer(serializers.Serializer):
    # Datos del usuario
    nombre = serializers.CharField(max_length=150)
    ci = serializers.CharField(max_length=20)
    correo = serializers.EmailField()
    telefono = serializers.CharField(max_length=20, allow_blank=True, required=False)
    password = serializers.CharField(write_only=True, required=False)  # por defecto "123"
    fecha_nacimiento = serializers.DateField(required=False, allow_null=True)

    # Apartamento: obligatorio y elegido manualmente
    apartamento_id = serializers.IntegerField(required=True)

    def validate(self, attrs):
        # Unicidad de email y CI
        if Usuario.objects.filter(email=attrs['correo']).exists():
            raise serializers.ValidationError({"correo": "Ya existe un usuario con este correo."})
        if Usuario.objects.filter(ci=attrs['ci']).exists():
            raise serializers.ValidationError({"ci": "Ya existe un usuario con este CI."})

        # Verificar apartamento existe (ya NO exigimos estado == DISPONIBLE)
        try:
            apto = Apartamento.objects.get(pk=attrs['apartamento_id'])
        except Apartamento.DoesNotExist:
            raise serializers.ValidationError({"apartamento_id": "El apartamento no existe."})
        
        attrs['__apartamento'] = apto
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        # Lock del apartamento para evitar condiciones de carrera
        apto = validated_data.pop('__apartamento')
        apto = Apartamento.objects.select_for_update().get(pk=apto.pk)

        nombre = validated_data.pop('nombre')
        correo = validated_data.pop('correo')
        ci = validated_data.pop('ci')
        telefono = validated_data.pop('telefono', '')
        fecha_nacimiento = validated_data.pop('fecha_nacimiento', None)
        raw_password = validated_data.pop('password', '123')  # default si no envían

        # Crear Usuario con rol RESIDENTE
        user = Usuario(
            email=correo,
            username=correo,  # cumple REQUIRED_FIELDS del AbstractUser
            ci=ci,
            nombre=nombre,
            telefono=telefono or None,
            fecha_nacimiento=fecha_nacimiento,
            rol=getattr(Usuario.Roles, 'RESIDENTE', 'RESIDENTE')
        )
        user.set_password(raw_password)
        user.is_active = True
        user.save()

        # Regla extra de seguridad: una residencia activa por usuario
        if Residencia.objects.filter(usuario=user, fecha_fin__isnull=True).exists():
            raise serializers.ValidationError("El usuario ya tiene una residencia activa.")

        # Crear Residencia (fecha_inicio = hoy)
        residencia = Residencia.objects.create(
            usuario=user,
            apartamento=apto,
            fecha_inicio=timezone.localdate()
        )

        # Nota: no modificamos el estado del apartamento aquí (queda como esté).
        return {"usuario": user, "residencia": residencia}

    def to_representation(self, instance):
        user = instance["usuario"]
        residencia = instance["residencia"]
        return {
            "usuario": {
                "id": user.id,
                "nombre": getattr(user, 'nombre', None),
                "ci": user.ci,
                "email": user.email,
                "telefono": user.telefono,
                "rol": getattr(user, 'rol', None),
                "fecha_nacimiento": user.fecha_nacimiento.isoformat() if user.fecha_nacimiento else None
            },
            "residencia": {
                "id": residencia.id,
                "apartamento": {
                    "id": residencia.apartamento.id,
                    "numero": residencia.apartamento.numero,
                    "bloque": residencia.apartamento.bloque,
                    "estado": residencia.apartamento.estado,
                },
                "fecha_inicio": residencia.fecha_inicio.isoformat(),
                "fecha_fin": residencia.fecha_fin.isoformat() if residencia.fecha_fin else None
            }
        }