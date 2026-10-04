from django.contrib import admin
from .models import Consulta


@admin.register(Consulta)
class ConsultaAdmin(admin.ModelAdmin):
    list_display = ('data', 'hora_inicio', 'atleta', 'profissional', 'tipo', 'status', 'prioridade')
    list_filter = ('status', 'tipo', 'prioridade', 'modalidade', 'projeto')
    search_fields = ('atleta__usuario__first_name', 'atleta__usuario__last_name', 'atleta__rm', 'motivo')
    date_hierarchy = 'data'
    ordering = ('-data', '-hora_inicio')
    readonly_fields = ('criado_em', 'atualizado_em', 'realizada_em', 'cancelada_em')