# app/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from app.views.auth import EmailOrUsernameTokenObtainPairView
from app.views.residencia import ResidenciaViewSet
from app.views.apartamento import ApartamentoViewSet
from app.views.residente import ResidenteAltaViewSet

urlpatterns = [

    path("auth/login/", EmailOrUsernameTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("residencias/", ResidenciaViewSet.as_view({'get': 'list', 'post': 'create'}), name="residencia-list"),
    path("apartamentos/", ApartamentoViewSet.as_view({'get': 'list', 'post': 'create'}), name="apartamento-list"),
    path("residentes/", ResidenteAltaViewSet.as_view({'post': 'create'}), name="residente-create"),
]
