from django.urls import path
from . import views

app_name = 'consultas'

urlpatterns = [
    path('', views.dashboard_consultas, name='dashboard_consultas'),
    path('lista/', views.lista_consultas, name='lista_consultas'),
    path('calendario/', views.calendario_consultas, name='calendario_consultas'),

    path('nova/', views.criar_consulta, name='criar_consulta'),
    path('<int:consulta_id>/', views.detalhes_consulta, name='detalhes_consulta'),
    path('<int:consulta_id>/editar/', views.editar_consulta, name='editar_consulta'),
    path('<int:consulta_id>/cancelar/', views.cancelar_consulta, name='cancelar_consulta'),

    # Ações de status (POST)
    path('<int:consulta_id>/confirmar/', views.confirmar_consulta, name='confirmar_consulta'),
    path('<int:consulta_id>/realizada/', views.marcar_realizada, name='marcar_realizada'),
    path('<int:consulta_id>/falta/', views.marcar_falta, name='marcar_falta'),
]