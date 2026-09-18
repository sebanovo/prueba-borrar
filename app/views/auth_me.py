from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        u = request.user
        data = {
            "id": u.id,
            "username": getattr(u, "username", ""),
            "email": getattr(u, "email", ""),
            # ajusta a tu modelo si tienes campos/roles extra:
            # "roles": getattr(u, "roles_list", []),
            # "nombre_completo": f"{u.first_name} {u.last_name}".strip(),
        }
        return Response(data)
