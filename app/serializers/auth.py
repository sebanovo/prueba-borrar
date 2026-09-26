from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

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
        # Solo guardamos el rol en el payload
        token["rol"] = user.rol
        return token
