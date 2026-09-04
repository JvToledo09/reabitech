from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Rotas Gerais e de Login
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

     # 🔥 Rota de emergência para alterar senha
    path('alterar-senha/', views.alterar_senha, name='alterar_senha'),

    # Dashboard por Perfil
    path('atleta/', views.dashboard_atleta, name='dashboard_atleta'),
    path('tecnico/', views.dashboard_tecnico, name='dashboard_tecnico'),
    path('coordenador/', views.dashboard_coordenador, name='dashboard_coordenador'),
    path('fisioterapeuta/', views.dashboard_fisioterapeuta, name='dashboard_fisioterapeuta'),
    path('psicologo/', views.dashboard_psicologo, name='dashboard_psicologo'),

    # 🔥 Nova rota de notificações
    path('notificacoes/', views.notificacoes, name='notificacoes'),

    # Views do Coordenador
    path('coordenador/atletas/', views.coordenador_atletas, name='coordenador_atletas'),
    path('coordenador/fisioterapia/', views.coordenador_fisioterapia, name='coordenador_fisioterapia'),
    path('coordenador/psicologia/', views.coordenador_psicologia, name='coordenador_psicologia'),
    path('coordenador/relatorios/', views.coordenador_relatorios, name='coordenador_relatorios'),
    path('coordenador/membros/', views.coordenador_membros, name='coordenador_membros'),
    
    # Rota de Adicionar Membro
    path('coordenador/membros/adicionar/', views.coordenador_adicionar_membro, name='coordenador_adicionar_membro'),
    
    # Rota de Detalhes do Membro (NOVA!)
    path('coordenador/membros/<int:membro_id>/', views.coordenador_detalhes_membro, name='coordenador_detalhes_membro'),

    # Views do Técnico
    path('tecnico/atletas/', views.tecnico_atletas, name='tecnico_atletas'),
    path('tecnico/desempenho/', views.tecnico_desempenho, name='tecnico_desempenho'),
    path('tecnico/recuperacao/', views.tecnico_recuperacao, name='tecnico_recuperacao'),

    # Views do Atleta
    path('atleta/recuperacao/', views.atleta_recuperacao, name='atleta_recuperacao'),
    path('atleta/psicologico/', views.atleta_psicologico, name='atleta_psicologico'),
    path('atleta/exercicios/', views.atleta_exercicios, name='atleta_exercicios'),

    # Views do Fisioterapeuta
    path('fisioterapeuta/atletas/', views.fisioterapeuta_atletas, name='fisioterapeuta_atletas'),
    path('fisioterapeuta/tratamentos/', views.fisioterapeuta_tratamentos, name='fisioterapeuta_tratamentos'),
    path('fisioterapeuta/evolucoes/', views.fisioterapeuta_evolucoes, name='fisioterapeuta_evolucoes'),

    # Views do Psicólogo
    path('psicologo/avaliacoes/', views.psicologo_avaliacoes, name='psicologo_avaliacoes'),
    path('psicologo/atletas/', views.psicologo_atletas, name='psicologo_atletas'),
]