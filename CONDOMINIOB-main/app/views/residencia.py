from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from app.models.residencia import Residencia
from app.serializers import ResidenciaSerializer

class ResidenciaViewSet(viewsets.ModelViewSet):
    queryset = Residencia.objects.select_related('usuario', 'apartamento').all()
    serializer_class = ResidenciaSerializer
    permission_classes = [permissions.IsAuthenticated]  # ajusta según tu política

    @action(detail=True, methods=['post'])
    def cerrar(self, request, pk=None):
        """
        Cierra una residencia poniendo fecha_fin = hoy (si no tiene).
        """
        instancia = self.get_object()
        if instancia.fecha_fin:
            return Response({"detail": "La residencia ya está cerrada."}, status=400)
        instancia.fecha_fin = timezone.localdate()
        instancia.save(update_fields=['fecha_fin'])
        return Response(self.get_serializer(instancia).data)
