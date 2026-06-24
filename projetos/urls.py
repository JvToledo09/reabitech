from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('selecionar/', views.selecionar_projeto, name='selecionar_projeto'),
    path('parceria/', views.nova_parceria, name='nova_parceria'),
    path('criar/', views.criar_projeto, name='criar_projeto'),
    path('projeto/<int:projeto_id>/', views.projeto_dashboard, name='projeto_dashboard'),
    path('login/projeto/<int:projeto_id>/', views.login_projeto, name='login_projeto'),
]