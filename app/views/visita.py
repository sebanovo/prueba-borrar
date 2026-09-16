from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_date
from app.models.visita import Visita
from app.serializers.visita import VisitaSerializer

class VisitaViewSet(ModelViewSet):
    queryset = Visita.objects.select_related("visitante", "apartamento", "vehiculo")
    serializer_class = VisitaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()

        # Filtros
        apartamento = self.request.query_params.get("apartamento")   
        visitante = self.request.query_params.get("visitante")      
        ci = self.request.query_params.get("ci")                    
        nombre = self.request.query_params.get("nombre")            
        placa = self.request.query_params.get("placa")             
        activas = self.request.query_params.get("activas")           
        fdesde = parse_date(self.request.query_params.get("fecha_desde") or "")
        fhasta = parse_date(self.request.query_params.get("fecha_hasta") or "")

        if apartamento:
            qs = qs.filter(apartamento_id=apartamento)
        if visitante:
            qs = qs.filter(visitante_id=visitante)
        if ci:
            qs = qs.filter(visitante__ci__iexact=ci)
        if nombre:
            qs = qs.filter(visitante__nombre__icontains=nombre)
        if placa:
            qs = qs.filter(vehiculo__placa__icontains=placa)
        if activas and activas.lower() == "true":
            qs = qs.filter(hora_salida__isnull=True)
        if fdesde:
            qs = qs.filter(fecha__gte=fdesde)
        if fhasta:
            qs = qs.filter(fecha__lte=fhasta)

        # Orden por defecto (recientes primero); acepta ?ordering=campo
        ordering = self.request.query_params.get("ordering")
        if ordering:
            qs = qs.order_by(ordering)
        else:
            qs = qs.order_by("-created_at")

        return qs

    @action(detail=False, methods=["get"], url_path="todos")
    def listar_todos(self, request):
        """Devuelve TODAS las visitas sin paginación (respetando filtros)."""
        qs = self.get_queryset()
        data = self.get_serializer(qs, many=True).data
        return Response(data)
