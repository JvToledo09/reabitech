from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Importando as views do dashboard para o login e logout na raiz
from dashboard import views as dashboard_views
from projetos import views as projetos_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # O dashboard cuida de todo o seu próprio fluxo (coordenador, atleta, etc) dentro de /dashboard/
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    
    # Rotas de Login e Logout na RAIZ do site (para os botões da navbar funcionarem)
    path('login/', dashboard_views.login_view, name='login'),
    path('logout/', dashboard_views.logout_view, name='logout'),
    
    # Projetos e a Landing Page na raiz
    path('projetos/', include('projetos.urls')),
    path('', projetos_views.lista_projetos_publicos, name='landing'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)