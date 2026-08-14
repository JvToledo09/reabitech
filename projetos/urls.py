from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_projetos_publicos, name='landing'),
    path('criar/', views.criar_projeto, name='criar_projeto'),
    path('entrar/<int:projeto_id>/', views.entrar_projeto, name='entrar_projeto'),
    path('convidar/', views.convidar_membro, name='convidar_membro'),
    path('aceitar-convite/<str:token>/', views.aceitar_convite, name='aceitar_convite'),
]