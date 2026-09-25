# ==============================================================================
# REABITECH — APP PROJETOS
# Admin Django
# ==============================================================================

from django.contrib import admin
from .models import Plano, Projeto, MembroProjeto, ConviteProjeto


# ==============================================================================
# PLANO
# ==============================================================================
@admin.register(Plano)
class PlanoAdmin(admin.ModelAdmin):
    list_display = (
        'nome', 'tipo', 'preco_mensal', 'max_usuarios',
        'max_projetos', 'destaque', 'ativo', 'ordem'
    )
    list_filter = ('tipo', 'destaque', 'ativo')
    search_fields = ('nome', 'descricao')
    ordering = ('ordem', 'preco_mensal')
    list_editable = ('destaque', 'ativo', 'ordem')

    fieldsets = (
        ('Identificação', {
            'fields': ('tipo', 'nome', 'descricao')
        }),
        ('Preço e Limites', {
            'fields': ('preco_mensal', 'max_usuarios', 'max_projetos')
        }),
        ('Módulos', {
            'fields': ('modulos_inclusos',)
        }),
        ('Exibição', {
            'fields': ('destaque', 'ordem', 'ativo')
        }),
    )


# ==============================================================================
# PROJETO
# ==============================================================================
@admin.register(Projeto)
class ProjetoAdmin(admin.ModelAdmin):
    list_display = (
        'nome', 'tipo', 'coordenador', 'plano',
        'total_membros', 'publico', 'ativo', 'criado_em'
    )
    list_filter = ('tipo', 'publico', 'ativo', 'plano')
    search_fields = (
        'nome', 'descricao',
        'coordenador__username', 'coordenador__email'
    )
    prepopulated_fields = {'slug': ('nome',)}
    readonly_fields = ('criado_em', 'atualizado_em')
    date_hierarchy = 'criado_em'
    ordering = ('-criado_em',)

    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'slug', 'tipo', 'descricao', 'logo')
        }),
        ('Configurações', {
            'fields': ('plano', 'coordenador', 'modulos_ativos')
        }),
        ('Visibilidade', {
            'fields': ('publico', 'ativo')
        }),
        ('Trial', {
            'fields': ('data_expiracao_trial',),
            'classes': ('collapse',)
        }),
        ('Auditoria', {
            'fields': ('criado_em', 'atualizado_em'),
            'classes': ('collapse',)
        }),
    )

    def total_membros(self, obj):
        return obj.membros.filter(ativo=True).count()
    total_membros.short_description = 'Membros ativos'


# ==============================================================================
# MEMBRO DO PROJETO
# ==============================================================================
@admin.register(MembroProjeto)
class MembroProjetoAdmin(admin.ModelAdmin):
    list_display = (
        'usuario', 'projeto', 'tipo', 'modalidade',
        'ativo', 'entrou_em'
    )
    list_filter = ('tipo', 'ativo', 'projeto')
    search_fields = (
        'usuario__username', 'usuario__email',
        'usuario__first_name', 'usuario__last_name',
        'projeto__nome'
    )
    autocomplete_fields = ('usuario', 'projeto')
    date_hierarchy = 'entrou_em'
    ordering = ('-entrou_em',)


# ==============================================================================
# CONVITE
# ==============================================================================
@admin.register(ConviteProjeto)
class ConviteProjetoAdmin(admin.ModelAdmin):
    list_display = (
        'email', 'projeto', 'tipo_membro',
        'aceito', 'criado_em', 'expiracao'
    )
    list_filter = ('aceito', 'tipo_membro', 'projeto')
    search_fields = ('email', 'projeto__nome', 'token')
    readonly_fields = ('token', 'criado_em')
    date_hierarchy = 'criado_em'
    ordering = ('-criado_em',)