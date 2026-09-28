from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter
from app.models.usuario import Usuario
from rest_framework.parsers import MultiPartParser, FormParser

from app.serializers.usuario import (
    UsuarioListSerializer,
    UsuarioCreateSerializer,
    UsuarioUpdateSerializer,
)

class UsuarioViewSet(ModelViewSet):
    queryset = Usuario.objects.all().order_by("id")
    serializer_class = UsuarioListSerializer

    # 👇 NECESARIO para archivos (foto)
    parser_classes = [MultiPartParser, FormParser]

    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["username", "email", "nombre", "ci", "rol"]
    ordering_fields = ["id", "username", "email", "nombre", "ci", "rol", "date_joined"]
    ordering = ["id"]

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]      # o IsAdminUser() si no quieres registro público
        return [IsAdminUser()]

    def get_serializer_class(self):
        if self.action == "create":
            return UsuarioCreateSerializer
        if self.action in ("update", "partial_update"):
            return UsuarioUpdateSerializer
        return UsuarioListSerializer

    # (Opcional) para construir foto_url absoluta en el serializer
    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx