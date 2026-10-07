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
    path('admin/', admin.site.urls),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),

    path('login/', dashboard_views.login_view, name='login'),
    path('logout/', dashboard_views.logout_view, name='logout'),

    path('projetos/', include('projetos.urls', namespace='projetos')),
    path('prontuario/', include('prontuario.urls', namespace='prontuario')),
    path('consultas/', include('consultas.urls')),
    path('mensageria/', include('mensageria.urls', namespace='mensageria')),
    path('analytics/', include('analytics.urls', namespace='analytics')),
    path('usuarios/', include('usuarios.urls', namespace='usuarios')),

    path('signup/', projetos_views.signup_saas, name='signup'),
    path('', projetos_views.landing_page, name='landing'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

handler404 = 'dashboard.views.erro_404'
handler500 = 'dashboard.views.erro_500'
handler403 = 'dashboard.views.erro_403'
