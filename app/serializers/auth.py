from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class EmailOrUsernameTokenObtainPairSerializer(TokenObtainPairSerializer):
    # anulamos el campo para que NO sea requerido
    username = serializers.CharField(required=False, allow_blank=True)
    # permitimos enviar email en su lugar
    email = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        # tomamos lo que venga en el body original (no en attrs aún)
        email = self.initial_data.get("email")
        username = self.initial_data.get("username")

        # si vino email y no username, traducimos email -> username
        if email and not username:
            try:
                u = User.objects.get(email__iexact=email)
                attrs["username"] = getattr(u, u.USERNAME_FIELD)  # normalmente "username"
            except User.DoesNotExist:
                # forzamos un username inválido para que falle con mensaje estándar
                attrs["username"] = "__no_user__"

        # si vino username, úsalo tal cual
        if username:
            attrs["username"] = username

        return super().validate(attrs)
