from rest_framework import mixins, viewsets, permissions
from app.serializers import ResidenteAltaSerializer
from app.models.usuario import Usuario

class ResidenteAltaViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    
    serializer_class = ResidenteAltaSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Usuario.objects.none()
