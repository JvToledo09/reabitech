# ==============================================================================
# REABITECH — URLS DA MENSAGERIA
# ==============================================================================

from django.urls import path
from . import views

app_name = 'mensageria'

urlpatterns = [
    # Página principal — lista de conversas
    path('', views.lista_conversas, name='lista_conversas'),

    # Criar nova conversa (DM ou grupo)
    path('nova/', views.nova_conversa, name='nova_conversa'),

    # Ver thread de uma conversa
    path('conversa/<int:conversa_id>/', views.ver_conversa, name='ver_conversa'),

    # API — total de não lidas (polling global)
    path('api/nao-lidas/', views.api_conversas_nao_lidas, name='api_nao_lidas'),

    # API — mensagens novas de uma conversa (polling 5s)
    path('api/conversa/<int:conversa_id>/novas/', views.api_mensagens_novas, name='api_mensagens_novas'),
]
