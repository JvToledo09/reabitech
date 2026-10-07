# ==============================================================================
# REABITECH — URLS DE ANALYTICS
# ==============================================================================

from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.dashboard_analitico, name='dashboard_analitico'),
    path('api/serie-temporal/', views.api_serie_temporal, name='api_serie_temporal'),
    path('api/distribuicoes/', views.api_distribuicoes, name='api_distribuicoes'),
    path('api/ranking-atletas/', views.api_ranking_atletas, name='api_ranking_atletas'),
    path('api/heatmap/', views.api_heatmap, name='api_heatmap'),
    path('exportar/csv/', views.exportar_serie_csv, name='exportar_serie_csv'),
]
