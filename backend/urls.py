from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from dashboard import views as dashboard_views
from projetos import views as projetos_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Landing page (raiz)
    path('', projetos_views.lista_projetos_publicos, name='landing'),
    
    # Autenticação
    path('login/', dashboard_views.login_view, name='login'),
    path('logout/', dashboard_views.logout_view, name='logout'),
    
    # Dashboards
    path('dashboard/', dashboard_views.dashboard, name='dashboard'),
    path('dashboard/atleta/', dashboard_views.dashboard_atleta, name='dashboard_atleta'),
    path('dashboard/tecnico/', dashboard_views.dashboard_tecnico, name='dashboard_tecnico'),
    path('dashboard/coordenador/', dashboard_views.dashboard_coordenador, name='dashboard_coordenador'),
    path('dashboard/fisioterapeuta/', dashboard_views.dashboard_fisioterapeuta, name='dashboard_fisioterapeuta'),
    path('dashboard/psicologo/', dashboard_views.dashboard_psicologo, name='dashboard_psicologo'),
    
    # Coordenador
    path('coordenador/atletas/', dashboard_views.coordenador_atletas, name='coordenador_atletas'),
    path('coordenador/fisioterapia/', dashboard_views.coordenador_fisioterapia, name='coordenador_fisioterapia'),
    path('coordenador/psicologia/', dashboard_views.coordenador_psicologia, name='coordenador_psicologia'),
    path('coordenador/relatorios/', dashboard_views.coordenador_relatorios, name='coordenador_relatorios'),
    path('coordenador/membros/', dashboard_views.coordenador_membros, name='coordenador_membros'),
    
    # Técnico
    path('tecnico/atletas/', dashboard_views.tecnico_atletas, name='tecnico_atletas'),
    path('tecnico/desempenho/', dashboard_views.tecnico_desempenho, name='tecnico_desempenho'),
    path('tecnico/recuperacao/', dashboard_views.tecnico_recuperacao, name='tecnico_recuperacao'),
    
    # Atleta
    path('atleta/recuperacao/', dashboard_views.atleta_recuperacao, name='atleta_recuperacao'),
    path('atleta/psicologico/', dashboard_views.atleta_psicologico, name='atleta_psicologico'),
    path('atleta/exercicios/', dashboard_views.atleta_exercicios, name='atleta_exercicios'),
    
    # Fisioterapeuta
    path('fisioterapeuta/atletas/', dashboard_views.fisioterapeuta_atletas, name='fisioterapeuta_atletas'),
    path('fisioterapeuta/tratamentos/', dashboard_views.fisioterapeuta_tratamentos, name='fisioterapeuta_tratamentos'),
    path('fisioterapeuta/evolucoes/', dashboard_views.fisioterapeuta_evolucoes, name='fisioterapeuta_evolucoes'),
    
    # Psicólogo
    path('psicologo/avaliacoes/', dashboard_views.psicologo_avaliacoes, name='psicologo_avaliacoes'),
    path('psicologo/atletas/', dashboard_views.psicologo_atletas, name='psicologo_atletas'),
    
    # Projetos
    path('projetos/', include('projetos.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)