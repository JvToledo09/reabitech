from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from dashboard import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('projetos.urls')),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Rotas do Coordenador
    path('coordenador/atletas/', views.coordenador_atletas, name='coordenador_atletas'),
    path('coordenador/fisioterapia/', views.coordenador_fisioterapia, name='coordenador_fisioterapia'),
    path('coordenador/psicologia/', views.coordenador_psicologia, name='coordenador_psicologia'),
    path('coordenador/relatorios/', views.coordenador_relatorios, name='coordenador_relatorios'),
    
    # Rotas do Técnico
    path('tecnico/atletas/', views.tecnico_atletas, name='tecnico_atletas'),
    path('tecnico/desempenho/', views.tecnico_desempenho, name='tecnico_desempenho'),
    path('tecnico/recuperacao/', views.tecnico_recuperacao, name='tecnico_recuperacao'),
    
    # Rotas do Atleta
    path('atleta/recuperacao/', views.atleta_recuperacao, name='atleta_recuperacao'),
    path('atleta/psicologico/', views.atleta_psicologico, name='atleta_psicologico'),
    path('atleta/exercicios/', views.atleta_exercicios, name='atleta_exercicios'),
    
    # Rotas dos Estagiários
    path('estagiario/atletas/', views.estagiario_atletas, name='estagiario_atletas'),
    path('estagiario/fisioterapia/', views.estagiario_fisioterapia, name='estagiario_fisioterapia'),
    path('estagiario/psicologia/', views.estagiario_psicologia, name='estagiario_psicologia'),
    path('estagiario/relatorios/', views.estagiario_relatorios, name='estagiario_relatorios'),
    path('estagiario/agenda/', views.estagiario_agenda, name='estagiario_agenda'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)