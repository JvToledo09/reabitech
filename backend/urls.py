from django.contrib import admin
from django.urls import path
from painel.views import home, login, dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home),
    path('login/', login),
    path('dashboard/', dashboard),
]