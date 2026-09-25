# ==============================================================================
# REABITECH — APP PROJETOS
# URLs
# ==============================================================================

from django.urls import path
from . import views

app_name = 'projetos'

urlpatterns = [
    # Landing page pública
    path('', views.landing_page, name='landing'),

    # Cadastro SaaS (cria conta + projeto + plano)
    path('signup/', views.signup_saas, name='signup'),

    # Criar projeto (usuário já logado)
    path('criar/', views.criar_projeto, name='criar_projeto'),

    # Entrar em um projeto existente
    path('entrar/<int:projeto_id>/', views.entrar_projeto, name='entrar_projeto'),

    # Convidar membro para o projeto
    path('convidar/', views.convidar_membro, name='convidar_membro'),

    # Aceitar convite
    path('aceitar-convite/<str:token>/', views.aceitar_convite, name='aceitar_convite'),
]