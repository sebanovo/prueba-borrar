from rest_framework import viewsets, permissions, mixins
from app.models.apartamento import Apartamento
from app.serializers import ApartamentoSerializer

class ApartamentoViewSet(mixins.CreateModelMixin,
                         mixins.ListModelMixin,   # opcional: listar
                         viewsets.GenericViewSet):
    queryset = Apartamento.objects.all()
    serializer_class = ApartamentoSerializer
    permission_classes = [permissions.IsAuthenticated]  # o IsAdminUser si solo admin crea
