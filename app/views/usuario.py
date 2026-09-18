from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny
from app.models.usuario import Usuario
from app.serializers.usuario import UsuarioCreateSerializer

class UsuarioViewSet(ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioCreateSerializer
    permission_classes = [AllowAny]  # cualquiera puede registrar (ajusta según tus reglas)
