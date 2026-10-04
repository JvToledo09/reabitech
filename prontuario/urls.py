from django.urls import path
from . import views

app_name = 'prontuario'

urlpatterns = [
    # ----- Geral -----
    path('', views.lista_prontuarios, name='lista_prontuarios'),
    path('novo/', views.selecionar_atleta_prontuario, name='selecionar_atleta_prontuario'),
    path('novo/<int:atleta_id>/', views.criar_prontuario, name='criar_prontuario'),
    path('relatorio-consolidado/pdf/', views.relatorio_consolidado_pdf, name='relatorio_consolidado_pdf'),

    # ----- Timeline Clínica -----
    path('timeline/', views.timeline_global, name='timeline_global'),
    path('timeline/<int:atleta_id>/', views.timeline_atleta, name='timeline_atleta'),

    # ----- Técnico (devem vir ANTES das rotas genéricas) -----
    path('tecnico/', views.tecnico_prontuarios_compartilhados, name='tecnico_prontuarios_compartilhados'),
    path('tecnico/<int:prontuario_id>/', views.tecnico_ver_prontuario, name='tecnico_ver_prontuario'),
    path('tecnico/<int:prontuario_id>/observacao/', views.tecnico_adicionar_observacao, name='tecnico_adicionar_observacao'),

    # ----- Prontuário individual -----
    path('<int:prontuario_id>/', views.dashboard_prontuario, name='dashboard_prontuario'),
    path('<int:prontuario_id>/imprimir/', views.imprimir_prontuario, name='imprimir_prontuario'),
    path('<int:prontuario_id>/pdf/', views.exportar_pdf_prontuario, name='exportar_pdf_prontuario'),

    # ----- Compartilhamento -----
    path('<int:prontuario_id>/compartilhar/', views.fisio_gerenciar_compartilhamento, name='fisio_gerenciar_compartilhamento'),
    path('<int:prontuario_id>/observacoes-tecnico/', views.fisio_ver_observacoes_tecnico, name='fisio_ver_observacoes_tecnico'),

    # ----- Triagens -----
    path('<int:prontuario_id>/triagem/nova/', views.criar_triagem, name='criar_triagem'),
    path('<int:prontuario_id>/triagens/', views.lista_triagens, name='lista_triagens'),
    path('triagem/<int:triagem_id>/editar/', views.editar_triagem, name='editar_triagem'),

    # ----- Objetivos -----
    path('<int:prontuario_id>/objetivo/novo/', views.criar_objetivo, name='criar_objetivo'),
    path('<int:prontuario_id>/objetivos/', views.lista_objetivos, name='lista_objetivos'),
    path('objetivo/<int:objetivo_id>/editar/', views.editar_objetivo, name='editar_objetivo'),
    path('objetivo/<int:objetivo_id>/deletar/', views.deletar_objetivo, name='deletar_objetivo'),

    # ----- Medicamentos -----
    path('<int:prontuario_id>/medicamento/novo/', views.criar_medicamento, name='criar_medicamento'),
    path('<int:prontuario_id>/medicamentos/', views.lista_medicamentos, name='lista_medicamentos'),
    path('medicamento/<int:medicamento_id>/editar/', views.editar_medicamento, name='editar_medicamento'),
    path('medicamento/<int:medicamento_id>/deletar/', views.deletar_medicamento, name='deletar_medicamento'),

    # ----- CIF -----
    path('<int:prontuario_id>/cif/nova/', views.criar_cif, name='criar_cif'),
    path('<int:prontuario_id>/cif/', views.lista_cif, name='lista_cif'),
    path('cif/<int:cif_id>/', views.detalhes_cif, name='detalhes_cif'),
    path('cif/<int:cif_id>/editar/', views.editar_cif, name='editar_cif'),

    # ----- Cardiorrespiratório -----
    path('<int:prontuario_id>/cardio/nova/', views.criar_cardio, name='criar_cardio'),
    path('<int:prontuario_id>/cardio/', views.lista_cardio, name='lista_cardio'),
    path('cardio/<int:cardio_id>/', views.detalhes_cardio, name='detalhes_cardio'),
    path('cardio/<int:cardio_id>/editar/', views.editar_cardio, name='editar_cardio'),

    # ----- Escalas de risco -----
    path('<int:prontuario_id>/escala/nova/', views.criar_escala, name='criar_escala'),
    path('<int:prontuario_id>/escalas/', views.lista_escalas, name='lista_escalas'),

    # ----- Relatórios diários -----
    path('<int:prontuario_id>/relatorio/novo/', views.criar_relatorio, name='criar_relatorio'),
    path('<int:prontuario_id>/relatorios/', views.lista_relatorios, name='lista_relatorios'),
    path('relatorio/<int:relatorio_id>/', views.detalhes_relatorio, name='detalhes_relatorio'),
    path('relatorio/<int:relatorio_id>/editar/', views.editar_relatorio, name='editar_relatorio'),

    # ----- Encaminhamentos -----
    path('<int:prontuario_id>/encaminhamento/novo/', views.criar_encaminhamento, name='criar_encaminhamento'),
    path('<int:prontuario_id>/encaminhamentos/', views.lista_encaminhamentos, name='lista_encaminhamentos'),
    path('encaminhamento/<int:encaminhamento_id>/editar/', views.editar_encaminhamento, name='editar_encaminhamento'),

    # ----- Exames -----
    path('<int:prontuario_id>/exame/novo/', views.criar_exame, name='criar_exame'),
    path('<int:prontuario_id>/exames/', views.lista_exames, name='lista_exames'),
    path('exame/<int:exame_id>/editar/', views.editar_exame, name='editar_exame'),

    # ----- Evoluções fisioterapêuticas -----
    path('<int:prontuario_id>/evolucao/nova/', views.criar_evolucao, name='criar_evolucao'),
    path('<int:prontuario_id>/evolucoes/', views.lista_evolucoes, name='lista_evolucoes'),
    path('evolucao/<int:evolucao_id>/', views.detalhes_evolucao, name='detalhes_evolucao'),
    path('evolucao/<int:evolucao_id>/editar/', views.editar_evolucao, name='editar_evolucao'),
]