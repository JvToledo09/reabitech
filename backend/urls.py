# ==============================================================================
# REABITECH — URLs RAIZ
# ==============================================================================

from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.contrib.sitemaps.views import sitemap
from django.http import HttpResponse
from backend.sitemaps import StaticViewSitemap
from django.conf import settings
from django.conf.urls.static import static

from dashboard import views as dashboard_views
from projetos import views as projetos_views


sitemaps = { 'static': StaticViewSitemap }

def robots_txt(request):
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /dashboard/",
        "Disallow: /prontuario/",
        "Disallow: /mensageria/",
        "Allow: /",
        "Sitemap: https://reabitech.onrender.com/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

def llms_txt(request):
    lines = [
        "# REABITECH - Plataforma de Reabilitacao",
        "> Sistema SaaS para gestao de reabilitacao fisica e emocional.",
        "",
        "## Paginas Publicas",
        "- [Home](/)",
        "- [Login](/login/)",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url='/static/images/projetos/esportetec.png', permanent=True)),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('llms.txt', llms_txt, name='llms_txt'),
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
