from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    path('admin/', admin.site.urls),

    path('', lambda request:
    render(request, 'dashboard.html')),

    path('dashboard/', lambda request:
    render(request, 'dashboard.html')),

    path('atletas/',
    include('atletas.urls')),

]

urlpatterns += static(
    settings.MEDIA_URL,
    document_root=settings.MEDIA_ROOT
)