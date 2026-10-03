from django.urls import path
from . import views

app_name = 'usuarios' 

urlpatterns = [
     path('auditoria/', views.auditoria_lista, name='auditoria_lista'),
    path('auditoria/<int:auditoria_id>/', views.auditoria_detalhes, name='auditoria_detalhes'),
    path('auditoria/usuario/<int:usuario_id>/', views.auditoria_usuario, name='auditoria_usuario'),
]