from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_atletas, name='lista_atletas'),

    path('novo/', views.novo_atleta, name='novo_atleta'),
]