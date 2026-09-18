from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # ============================================
    # Rotas Gerais
    # ============================================
    path('', views.dashboard, name='dashboard'),
    path('alterar-senha/', views.alterar_senha, name='alterar_senha'),

    # ============================================
    # Dashboards por Perfil
    # ============================================
    path('atleta/', views.dashboard_atleta, name='dashboard_atleta'),
    path('tecnico/', views.dashboard_tecnico, name='dashboard_tecnico'),
    path('coordenador/', views.dashboard_coordenador, name='dashboard_coordenador'),
    path('fisioterapeuta/', views.dashboard_fisioterapeuta, name='dashboard_fisioterapeuta'),
    path('psicologo/', views.dashboard_psicologo, name='dashboard_psicologo'),

    # ============================================
    # Views do Coordenador
    # ============================================
    path('coordenador/atletas/', views.coordenador_atletas, name='coordenador_atletas'),
    path('coordenador/fisioterapia/', views.coordenador_fisioterapia, name='coordenador_fisioterapia'),
    path('coordenador/psicologia/', views.coordenador_psicologia, name='coordenador_psicologia'),
    path('coordenador/relatorios/', views.coordenador_relatorios, name='coordenador_relatorios'),
    path('coordenador/membros/', views.coordenador_membros, name='coordenador_membros'),
    path('coordenador/membros/adicionar/', views.coordenador_adicionar_membro, name='coordenador_adicionar_membro'),
    path('coordenador/membros/<int:membro_id>/', views.coordenador_detalhes_membro, name='coordenador_detalhes_membro'),

    # ============================================
    # Views do Técnico
    # ============================================
    path('tecnico/atletas/', views.tecnico_atletas, name='tecnico_atletas'),
    path('tecnico/desempenho/', views.tecnico_desempenho, name='tecnico_desempenho'),
    path('tecnico/recuperacao/', views.tecnico_recuperacao, name='tecnico_recuperacao'),
    path('tecnico/atleta/<int:atleta_id>/', views.tecnico_detalhes_atleta, name='tecnico_detalhes_atleta'),

    # ============================================
    # Views do Atleta
    # ============================================
    path('atleta/recuperacao/', views.atleta_recuperacao, name='atleta_recuperacao'),
    path('atleta/psicologico/', views.atleta_psicologico, name='atleta_psicologico'),
    path('atleta/exercicios/', views.atleta_exercicios, name='atleta_exercicios'),

    # ============================================
    # Views do Fisioterapeuta
    # ============================================
    path('fisioterapeuta/atletas/', views.fisioterapeuta_atletas, name='fisioterapeuta_atletas'),
    path('fisioterapeuta/tratamentos/', views.fisioterapeuta_tratamentos, name='fisioterapeuta_tratamentos'),
    path('fisioterapeuta/evolucoes/', views.fisioterapeuta_evolucoes, name='fisioterapeuta_evolucoes'),
    path('fisioterapeuta/todos-atletas/', views.fisioterapeuta_todos_atletas, name='fisioterapeuta_todos_atletas'),
    path('fisioterapeuta/criar-lesao/<int:atleta_id>/', views.fisioterapeuta_criar_lesao, name='fisioterapeuta_criar_lesao'),
    path('fisioterapeuta/criar-tratamento/<int:lesao_id>/', views.fisioterapeuta_criar_tratamento, name='fisioterapeuta_criar_tratamento'),
    path('fisioterapeuta/lesao/<int:lesao_id>/', views.fisioterapeuta_detalhes_lesao, name='fisioterapeuta_detalhes_lesao'),
    path('fisioterapeuta/adicionar-exercicio/<int:tratamento_id>/', views.fisioterapeuta_adicionar_exercicio, name='fisioterapeuta_adicionar_exercicio'),
    path('fisioterapeuta/registrar-evolucao/<int:atleta_id>/', views.fisioterapeuta_registrar_evolucao, name='fisioterapeuta_registrar_evolucao'),

    # ============================================
    # Views do Psicólogo
    # ============================================
    path('psicologo/atletas/', views.psicologo_atletas, name='psicologo_atletas'),
    path('psicologo/avaliacoes/', views.psicologo_avaliacoes, name='psicologo_avaliacoes'),
    path('psicologo/nova-avaliacao/<int:atleta_id>/', views.psicologo_nova_avaliacao, name='psicologo_nova_avaliacao'),
    path('psicologo/avaliacoes/<int:avaliacao_id>/', views.psicologo_detalhes_avaliacao, name='psicologo_detalhes_avaliacao'),
    path('psicologo/questionario/<int:atleta_id>/', views.psicologo_novo_questionario, name='psicologo_novo_questionario'),

    # ============================================
    # Notificações
    # ============================================
    path('notificacoes/', views.notificacoes, name='notificacoes'),
    path('notificacoes/<int:notificacao_id>/lida/', views.marcar_notificacao_lida, name='marcar_notificacao_lida'),
    path('notificacoes/marcar-todas/', views.marcar_todas_lidas, name='marcar_todas_lidas'),
]