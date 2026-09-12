# app/serializers.py
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from app.models.usuario import Usuario
from app.models.apartamento import Apartamento
from app.models.residencia import Residencia
from django.db import transaction
from django.utils import timezone
from app.models.propiedad import Propiedad


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
        
class UsuarioResidenteCreateSerializer(serializers.ModelSerializer):
    # Renombramos "email" a "correo" para el payload
    correo = serializers.EmailField(source='email')
    password = serializers.CharField(write_only=True, required=False)  # default "123"

    class Meta:
        model = Usuario
        fields = ('id', 'nombre', 'ci', 'correo', 'telefono', 'password', 'fecha_nacimiento', 'rol')
        read_only_fields = ('id', 'rol')

    def validate(self, attrs):
        email = attrs['email']
        ci = attrs['ci']
        if Usuario.objects.filter(email=email).exists():
            raise serializers.ValidationError({"correo": "Ya existe un usuario con este correo."})
        if Usuario.objects.filter(ci=ci).exists():
            raise serializers.ValidationError({"ci": "Ya existe un usuario con este CI."})
        return attrs

    def create(self, validated_data):
        raw_password = validated_data.pop('password', '123')
        # Aseguramos username para AbstractUser
        if not validated_data.get('username'):
            validated_data['username'] = validated_data['email']
        # Rol residente
        validated_data['rol'] = getattr(Usuario.Roles, 'RESIDENTE', 'RESIDENTE')

        user = Usuario(**validated_data)
        user.set_password(raw_password)
        user.is_active = True
        user.save()
        return user

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "nombre": instance.nombre,
            "ci": instance.ci,
            "correo": instance.email,
            "telefono": instance.telefono,
            "rol": instance.rol,
            "fecha_nacimiento": instance.fecha_nacimiento.isoformat() if instance.fecha_nacimiento else None
        }
        
class ResidenciaAsignarSerializer(serializers.Serializer):
    usuario_id = serializers.IntegerField()
    apartamento_id = serializers.IntegerField()
    fecha_inicio = serializers.DateField(required=False)  # default: hoy

    def validate(self, attrs):
        # Usuario existente
        try:
            usuario = Usuario.objects.get(pk=attrs['usuario_id'])
        except Usuario.DoesNotExist:
            raise serializers.ValidationError({"usuario_id": "El usuario no existe."})

        # Apartamento existente
        try:
            apartamento = Apartamento.objects.get(pk=attrs['apartamento_id'])
        except Apartamento.DoesNotExist:
            raise serializers.ValidationError({"apartamento_id": "El apartamento no existe."})

        # Regla: solo una residencia ACTIVA por usuario
        if Residencia.objects.filter(usuario=usuario, fecha_fin__isnull=True).exists():
            raise serializers.ValidationError("El usuario ya tiene una residencia activa.")

        attrs['__usuario'] = usuario
        attrs['__apartamento'] = apartamento
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        usuario = validated_data.pop('__usuario')
        apartamento = validated_data.pop('__apartamento')

        # Lock de apartamento por seguridad (evita carreras si luego decides validar capacidad/estado)
        apartamento = Apartamento.objects.select_for_update().get(pk=apartamento.pk)

        fecha_inicio = validated_data.pop('fecha_inicio', None) or timezone.localdate()

        residencia = Residencia.objects.create(
            usuario=usuario,
            apartamento=apartamento,
            fecha_inicio=fecha_inicio
        )

        # (Opcional) Cambiar estado del apartamento aquí si quisieras:
        # apartamento.estado = "OCUPADO"
        # apartamento.save(update_fields=["estado"])

        return residencia

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "usuario": {
                "id": instance.usuario.id,
                "nombre": getattr(instance.usuario, 'nombre', None),
                "ci": instance.usuario.ci,
                "email": instance.usuario.email,
                "telefono": instance.usuario.telefono,
                "rol": getattr(instance.usuario, 'rol', None),
                "fecha_nacimiento": instance.usuario.fecha_nacimiento.isoformat() if instance.usuario.fecha_nacimiento else None
            },
            "apartamento": {
                "id": instance.apartamento.id,
                "numero": instance.apartamento.numero,
                "bloque": instance.apartamento.bloque,
                "estado": instance.apartamento.estado,
            },
            "fecha_inicio": instance.fecha_inicio.isoformat(),
            "fecha_fin": instance.fecha_fin.isoformat() if instance.fecha_fin else None
        }


class UsuarioPropietarioCreateSerializer(serializers.ModelSerializer):
    correo = serializers.EmailField(source='email')
    password = serializers.CharField(write_only=True, required=False)  # default "123"

    class Meta:
        model = Usuario
        fields = ('id', 'nombre', 'ci', 'correo', 'telefono', 'password', 'fecha_nacimiento', 'rol')
        read_only_fields = ('id', 'rol')

    def validate(self, attrs):
        email = attrs['email']
        ci = attrs['ci']
        if Usuario.objects.filter(email=email).exists():
            raise serializers.ValidationError({"correo": "Ya existe un usuario con este correo."})
        if Usuario.objects.filter(ci=ci).exists():
            raise serializers.ValidationError({"ci": "Ya existe un usuario con este CI."})
        return attrs

    def create(self, validated_data):
        raw_password = validated_data.pop('password', '123')
        if not validated_data.get('username'):
            validated_data['username'] = validated_data['email']
        validated_data['rol'] = getattr(Usuario.Roles, 'DUEÑO', 'DUEÑO')  # o "PROPIETARIO" si así lo nombras

        user = Usuario(**validated_data)
        user.set_password(raw_password)
        user.is_active = True
        user.save()
        return user

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "nombre": instance.nombre,
            "ci": instance.ci,
            "correo": instance.email,
            "telefono": instance.telefono,
            "rol": instance.rol,
            "fecha_nacimiento": instance.fecha_nacimiento.isoformat() if instance.fecha_nacimiento else None
        }
        
class PropiedadAsignarSerializer(serializers.Serializer):
    usuario_id = serializers.IntegerField()
    apartamento_id = serializers.IntegerField()
    fecha_inicio = serializers.DateField(required=False)   # default: hoy
    fecha_fin = serializers.DateField(required=False, allow_null=True)
    vive = serializers.BooleanField(required=False, default=False)   # si vive, crear Residencia

    def validate(self, attrs):
        # Usuario
        try:
            usuario = Usuario.objects.get(pk=attrs['usuario_id'])
        except Usuario.DoesNotExist:
            raise serializers.ValidationError({"usuario_id": "El usuario no existe."})

        # Apartamento
        try:
            apartamento = Apartamento.objects.get(pk=attrs['apartamento_id'])
        except Apartamento.DoesNotExist:
            raise serializers.ValidationError({"apartamento_id": "El apartamento no existe."})

        fi = attrs.get('fecha_inicio')
        ff = attrs.get('fecha_fin')

        # Reglas básicas de fechas
        if ff and fi and ff < fi:
            raise serializers.ValidationError({"fecha_fin": "No puede ser anterior a fecha_inicio."})

        # Evitar dos propietarios activos en mismo apartamento
        if not ff:
            activo_otro = Propiedad.objects.filter(apartamento=apartamento, fecha_fin__isnull=True).exists()
            if activo_otro:
                raise serializers.ValidationError({"apartamento_id": "El apartamento ya tiene un propietario activo."})

        # Evitar solapamiento de rangos (simple) con otras propiedades del mismo apartamento
        # [fi, ff] solapa con cualquiera que cumpla:
        # (ff_nueva is null o ff_nueva >= fi_existente) y (ff_existente is null o ff_existente >= fi_nueva)
        fi_nueva = fi or timezone.localdate()
        qs = Propiedad.objects.filter(apartamento=apartamento)
        for p in qs:
            fi_old = p.fecha_inicio
            ff_old = p.fecha_fin
            # si no hay fin, tómalo como abierto
            ff_cmp = ff or timezone.localdate().replace(year=9999)  # "infinito" simple
            ff_old_cmp = ff_old or timezone.localdate().replace(year=9999)
            if (fi_nueva <= ff_old_cmp) and (fi_old <= ff_cmp):
                raise serializers.ValidationError({"apartamento_id": "Rango de propiedad se solapa con otra existente."})

        attrs['__usuario'] = usuario
        attrs['__apartamento'] = apartamento
        attrs['__fi'] = fi_nueva
        attrs['__ff'] = ff
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        usuario = validated_data.pop('__usuario')
        apartamento = validated_data.pop('__apartamento')
        fi = validated_data.pop('__fi')
        ff = validated_data.pop('__ff')
        vive = validated_data.get('vive', False)

        # Lock apartamento por seguridad
        apartamento = Apartamento.objects.select_for_update().get(pk=apartamento.pk)

        # Crear Propiedad
        propiedad = Propiedad.objects.create(
            usuario=usuario,
            apartamento=apartamento,
            fecha_inicio=fi,
            fecha_fin=ff
        )

        # Si VIVE, crear Residencia (si no tiene activa)
        residencia = None
        if vive:
            if Residencia.objects.filter(usuario=usuario, fecha_fin__isnull=True).exists():
                raise serializers.ValidationError("El usuario ya tiene una residencia activa.")
            residencia = Residencia.objects.create(
                usuario=usuario,
                apartamento=apartamento,
                fecha_inicio=fi
            )
            # Si quieres, aquí puedes cambiar estado del apartamento a OCUPADO
            # apartamento.estado = "OCUPADO"
            # apartamento.save(update_fields=['estado'])

        return {"propiedad": propiedad, "residencia": residencia}

    def to_representation(self, instance):
        propiedad = instance["propiedad"]
        residencia = instance["residencia"]
        data = {
            "propiedad": {
                "id": propiedad.id,
                "usuario": {
                    "id": propiedad.usuario.id,
                    "nombre": getattr(propiedad.usuario, 'nombre', None),
                    "email": propiedad.usuario.email,
                    "rol": getattr(propiedad.usuario, 'rol', None),
                },
                "apartamento": {
                    "id": propiedad.apartamento.id,
                    "numero": propiedad.apartamento.numero,
                    "bloque": propiedad.apartamento.bloque,
                    "estado": propiedad.apartamento.estado,
                },
                "fecha_inicio": propiedad.fecha_inicio.isoformat(),
                "fecha_fin": propiedad.fecha_fin.isoformat() if propiedad.fecha_fin else None
            }
        }
        if residencia:
            data["residencia"] = {
                "id": residencia.id,
                "fecha_inicio": residencia.fecha_inicio.isoformat(),
                "fecha_fin": residencia.fecha_fin.isoformat() if residencia.fecha_fin else None
            }
        return data