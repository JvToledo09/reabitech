# ==============================================================================
# REABITECH — URLs RAIZ
# ==============================================================================

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from dashboard import views as dashboard_views
from projetos import views as projetos_views

urlpatterns = [
    # Admin do Django
    path('admin/', admin.site.urls),

    # Dashboard (namespace)
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),

    # Autenticação na raiz
    path('login/', dashboard_views.login_view, name='login'),
    path('logout/', dashboard_views.logout_view, name='logout'),

    # App de projetos (namespace)
    path('projetos/', include('projetos.urls', namespace='projetos')),

    # Atalho direto para o signup na raiz
    path('signup/', projetos_views.signup_saas, name='signup'),

    # Landing page na raiz
    path('', projetos_views.landing_page, name='landing'),
]

# Servir arquivos estáticos e de mídia em desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)