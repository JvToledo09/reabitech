from django.contrib import admin
from .models import Plano, Projeto, ProfissionalProjeto, AtletaProjeto, Parceria, Assinatura

@admin.register(Plano)
class PlanoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'valor_mensal', 'max_projetos', 'max_atletas', 'destaque']
    list_filter = ['destaque', 'tem_fisioterapia', 'tem_psicologia']

@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'plano', 'status', 'ativo', 'data_vencimento']
    list_filter = ['status', 'ativo', 'plano']
    search_fields = ['nome', 'slug', 'descricao']
    prepopulated_fields = {'slug': ('nome',)}

@admin.register(ProfissionalProjeto)
class ProfissionalProjetoAdmin(admin.ModelAdmin):
    list_display = ['projeto', 'usuario', 'tipo', 'ativo']
    list_filter = ['tipo', 'ativo']

@admin.register(AtletaProjeto)
class AtletaProjetoAdmin(admin.ModelAdmin):
    list_display = ['projeto', 'atleta', 'ativo']
    list_filter = ['ativo']

@admin.register(Parceria)
class ParceriaAdmin(admin.ModelAdmin):
    list_display = ['nome_projeto', 'nome_parceiro', 'plano_interesse', 'status', 'data_solicitacao']
    list_filter = ['status', 'plano_interesse']

@admin.register(Assinatura)
class AssinaturaAdmin(admin.ModelAdmin):
    list_display = ['projeto', 'plano', 'data_inicio', 'data_fim', 'status']
    list_filter = ['status', 'plano']