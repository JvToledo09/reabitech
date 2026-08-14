from django.contrib import admin
from .models import Plano, Projeto, MembroProjeto, ConviteProjeto

@admin.register(Plano)
class PlanoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'preco_mensal', 'max_usuarios', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('nome',)

@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo', 'coordenador', 'data_criacao', 'ativo', 'publico')
    list_filter = ('tipo', 'ativo', 'publico')
    search_fields = ('nome', 'descricao')
    raw_id_fields = ('coordenador',)

@admin.register(MembroProjeto)
class MembroProjetoAdmin(admin.ModelAdmin):
    list_display = ('projeto', 'usuario', 'tipo', 'data_entrada', 'ativo')
    list_filter = ('tipo', 'ativo', 'projeto')
    search_fields = ('usuario__username', 'usuario__email')
    raw_id_fields = ('projeto', 'usuario')

@admin.register(ConviteProjeto)
class ConviteProjetoAdmin(admin.ModelAdmin):
    list_display = ('projeto', 'email', 'tipo_membro', 'criado_em', 'expiracao', 'aceito')
    list_filter = ('tipo_membro', 'aceito', 'projeto')
    search_fields = ('email',)
    raw_id_fields = ('projeto',)